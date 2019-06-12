import whiteboard_client as wbc
import helper_functions as helper
import urllib.request
import json
import config
from pathlib import Path
from ca_logging import log


class DM(wbc.WhiteBoardClient):
    def __init__(self, subscribes, publishes, clientid):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "DM" + clientid, subscribes, publishes)

        self.client_id = clientid

        self.currState = "start"
        # Do we store the users preferences in a user model?
        self.store_pref = True

        self.from_NLU = None
        self.from_SA = None

        self.movie = {'title': "", 'year': "", 'plot': "", 'actors': [], 'genres': [], 'poster': ""}
        self.nodes = {}
        self.user_model = {"liked_cast": [], "disliked_cast": [], "liked_genres": [], 'disliked_genres': [],
                           'liked_movies': [], 'disliked_movies': []}
        self.load_model(config.DM_MODEL)
        self.load_user_model(config.USER_MODELS, clientid)

    # Parse the model.csv file and transform that into a dict of Nodes representing the scenario
    def load_model(self, path):
        with open(path) as f:
            for line in f:
                line_input = line.replace('\n', '')
                line_input = line_input.split(",")
                node = DMNode(line_input[0], line_input[1], line_input[2])
                for i in range(3, len(line_input)):
                    if "-" in line_input[i]:
                        node.add(line_input[i])
                self.nodes[node.stateName] = node

    def save_user_model(self):
        file = config.USER_MODELS + self.client_id + ".prefs"
        with open(file, 'w') as outfile:
            json.dump(self.user_model, outfile)

    def load_user_model(self, path, client_id):
        file = Path(path + client_id + ".prefs")
        if file.is_file():
            with open(file) as json_file:
                self.user_model = json.load(json_file)

    def treat_message(self, msg, topic):
        self.movie['poster'] = None
        if "SA" in topic:
            self.from_SA = msg
        elif "NLU" in topic:
            self.from_NLU = json.loads(msg)
        # Wait for both SA and NLU messages before sending something back to the whiteboard
        if self.from_NLU and self.from_SA:

            # Store entities (actors,directors, genres) in the user frame
            if self.store_pref and "inform" in self.from_NLU['intent']:
                if '+' in self.from_NLU['polarity']:
                    if 'cast' in self.from_NLU['entity_type']:
                        self.user_model["liked_cast"].append(self.from_NLU['entity'])
                    elif 'genre' in self.from_NLU['entity_type']:
                        self.user_model["liked_genres"].append(self.from_NLU['entity'])
                elif '-' in self.from_NLU['polarity']:
                    if 'cast' in self.from_NLU['entity_type']:
                        self.user_model["disliked_cast"].append(self.from_NLU['entity'])
                    elif 'genre' in self.from_NLU['entity_type']:
                        self.user_model["disliked_genre"].append(self.from_NLU['entity'])

            next_state = self.nodes.get(self.currState).get_action(self.from_NLU['intent'])

            if self.currState in ("inform(movie)", "inform(plot)", "inform(actor)", "inform(genre)"):
                if "yes" in self.from_NLU['intent']:
                    self.user_model['liked_movies'].append(self.movie['title'])
                elif any(s in self.from_NLU['intent'] for s in ('request(another)', 'inform(watched)', 'no')):
                    self.user_model['disliked_movies'].append(self.movie['title'])

            # Get a movie recommendation title
            if "inform(movie)" in next_state:
                self.movie['title'] = self.recommend()
                self.set_movie_info(self.movie['title'])

            # if the user comes back
            if next_state == 'greeting' and (self.user_model['liked_movies'] or self.user_model['disliked_movies']):
                next_state = "greet_back"

            # saves the user model at the end of the interaction
            if next_state == 'bye' and config.SAVE_USER_MODEL:
                self.save_user_model()

            prev_state = self.currState
            self.currState = next_state
            new_msg = self.msg_to_json(next_state, self.movie, self.from_NLU, prev_state, self.user_model)
            self.from_NLU = None
            self.from_SA = None
            self.publish(new_msg)

    def msg_to_json(self, intention, movie, user_intent, previous_intent, user_frame):
        frame = {'intent': intention, 'movie': movie, 'user_intent': user_intent, 'previous_intent': previous_intent, 'user_model': user_frame}
        json_msg = json.dumps(frame)
        return json_msg

    def recommend(self):
        movies_list = self.queryMoviesList()
        for movie in movies_list:
            if movie['title'] not in self.user_model['liked_movies'] and movie['title'] not in self.user_model['disliked_movies']:
                if config.HIGH_QUALITY_POSTER:
                    self.movie['poster'] = config.MOVIEDB_POSTER_PATH + movie['poster_path']
                return movie['title']

    def queryMoviesList(self):
        # Todo Smart blending to get a recommendation matching with both genre and cast
        movies_with_cast_list = []
        movies_with_genres_list = []
        if not self.user_model['liked_genres'] and not self.user_model['liked_cast']:
            query_url = config.MOVIEDB_SEARCH_MOVIE_ADDRESS + config.MOVIEDB_KEY + config.MOVIE_DB_PROPERTY
            data = urllib.request.urlopen(query_url)
            result = data.read()
            movies = json.loads(result)
            return movies['results']
        if self.user_model['liked_genres']:
            genre_id = self.get_genre_id(self.user_model['liked_genres'][-1].lower())
            query_url = config.MOVIEDB_SEARCH_MOVIE_ADDRESS + config.MOVIEDB_KEY + "&with_genres=" + str(genre_id) + config.MOVIE_DB_PROPERTY
            data = urllib.request.urlopen(query_url)
            result = data.read()
            movies = json.loads(result)
            movies_with_genres_list = movies['results']
        if self.user_model['liked_cast']:
            cast_id = self.get_cast_id(self.user_model['liked_cast'][-1].lower())
            query_url = config.MOVIEDB_SEARCH_MOVIE_ADDRESS + config.MOVIEDB_KEY + "&with_people=" + str(cast_id) + config.MOVIE_DB_PROPERTY
            data = urllib.request.urlopen(query_url)
            result = data.read()
            movies = json.loads(result)
            movies_with_cast_list = movies['results']
        if movies_with_genres_list:
            if movies_with_cast_list:
                if len(movies_with_genres_list) > len(movies_with_cast_list):
                    smallest_list = movies_with_cast_list
                    biggest_list = movies_with_genres_list
                else:
                    smallest_list = movies_with_genres_list
                    biggest_list = movies_with_cast_list

                j = 0
                movies_blended_list = []
                for i in range(len(smallest_list)):
                    movies_blended_list.append(smallest_list[i])
                    movies_blended_list.append(biggest_list[i])
                    j = i

                for k in range(j, len(biggest_list)):
                    movies_blended_list.append(biggest_list[k])

                return movies_blended_list
            else:
                return movies_with_genres_list
        else:
            return movies_with_cast_list

    def get_genre_id(self, genre_name):
        return {
            'action': 28,
            'adventure': 12,
            'animation': 16,
            'comedy': 35,
            'comedies': 35,
            'crime': 80,
            'documentary': 99,
            'drama': 18,
            'family': 10751,
            'fantasy': 14,
            'history': 36,
            'horror': 27,
            'music': 10402,
            'romance': 10749,
            'romantic': 10749,
            'sci-fi': 878,
            'syfy': 878,
            'thriller': 53,
            'war': 10752,
            'western': 37
        }.get(genre_name, 0)

    def get_cast_id(self, cast_name):
        cast_name = cast_name.replace(" ", "%20")
        query_url = config.MOVIEDB_SEARCH_PERSON_ADDRESS + config.MOVIEDB_KEY + "&query=" + cast_name
        data = urllib.request.urlopen(query_url)
        result = data.read()
        movies = json.loads(result)
        return int(movies['results'][0]['id'])

    def set_movie_info(self, movie_name):
        movie_name = movie_name.replace(" ", "%20")
        movie_name = movie_name.replace("é", "e")
        omdbURL = config.OMDB_SEARCH_MOVIE_INFO + movie_name + "&r=json" + "&apikey=" + config.OMDB_KEY
        data = urllib.request.urlopen(omdbURL)
        result = data.read()
        movie_info = json.loads(result)
        self.movie['plot'] = movie_info.get("Plot")
        self.movie['actors'] = movie_info.get("Actors")
        self.movie['genres'] = movie_info.get("Genre")
        if config.HIGH_QUALITY_POSTER is False:
            self.movie['poster'] = movie_info.get("Poster")


# A node corresponds to a specific state of the dialogue. It contains:
# - a state ID (int)
# - a state name (String)
# - a default state (String) which represents the next state by default, whatever the user says.
# - a set of rules (dict) mapping a specific user intent to another state (e.g. yes-inform() means that if the user says
#   yes, the next state will be inform())
class DMNode:
    def __init__(self, state_name, state_default, state_ack):
        self.stateName = state_name
        self.stateDefault = state_default
        if state_ack.lower() == "true":
            self.stateAck = True
        else:
            self.stateAck = False
        self.rules = {}

    def add(self, string):
        intents = string.split("-")
        self.rules[intents[0]] = intents[1]

    def get_action(self, user_intent):
        if user_intent in self.rules:
            return self.rules.get(user_intent)
        else:
            return self.stateDefault
