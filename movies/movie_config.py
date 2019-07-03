
####################################################################################################
##                                          Resources Path                                        ##
####################################################################################################

DM_MODEL = "movies/resources/dm/model.csv"
USER_MODELS = "movies/resources/user_models/"
NLG_SENTENCE_DB = "movies/resources/nlg/sentence_db.csv"
NLG_ACK_DB = "movies/resources/nlg/ack_db.csv"
ACTORS_LEXICON = "movies/resources/nlu/actor2id.lexicon"
DIRECTORS_LEXICON = "movies/resources/nlu/director2id.lexicon"
GENRES_LEXICON = "movies/resources/nlu/genre2id.lexicon"
GRAMMAR_PATH = "movies/resources/nlg/grammar/"

####################################################################################################
##                                      Movie recommendation config                               ##
####################################################################################################
MOVIEDB_KEY = "6e3c2d4a2501c86cd7e0571ada291f55"
MOVIEDB_SEARCH_MOVIE_ADDRESS = "https://api.themoviedb.org/3/discover/movie?api_key="
MOVIE_DB_PROPERTY = "&sort_by=popularity.desc"
MOVIEDB_SEARCH_PERSON_ADDRESS = "https://api.themoviedb.org/3/search/person?api_key="
MOVIEDB_POSTER_PATH = "https://image.tmdb.org/t/p/original/"
OMDB_SEARCH_MOVIE_INFO = "http://www.omdbapi.com/?t="
OMDB_KEY = "be72fd68"
HIGH_QUALITY_POSTER = True

####################################################################################################
##                                          Other config                                          ##
####################################################################################################
SAVE_USER_MODEL = False
NLG_USE_ACKS = True
NLG_USE_ACKS_CS = True
NLG_USE_CS = True
NLG_USE_EXPLANATIONS = True
CS_LABELS = ["SD", "PR", "HE", "VSN", "NONE", 'QESD']
EXPLANATION_TYPE_LABELS = ["MF", "TPO", "PO", "PE"]
EXPLANATION_TYPE_PROBA = [.37, .07, .39, .17]
MF_EXPLANATION_LABELS = ["C", "G", "P", "A", "O"]
MF_EXPLANATION_PROBA = [.108, .243, .459, .055, .135]
TPO_EXPLANATION_LABELS = ["B", "S"]
TPO_EXPLANATION_PROBA = [.571, .429]
PO_EXPLANATION_LABELS = ["POS", "ANA", "SO"]
PO_EXPLANATION_PROBA = [.513, .308, .179]
PE_EXPLANATION_LABELS = ["A", "L", "C"]
PE_EXPLANATION_PROBA = [.177, .529, .294]



