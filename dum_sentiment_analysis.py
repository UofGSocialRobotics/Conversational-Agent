import whiteboard_client as wbc
from ca_logging import log
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class SentimentAnalysis(wbc.WhiteBoardClient):
    def __init__(self, name, msg_subscribe_types, msg_publish_type):
        wbc.WhiteBoardClient.__init__(self, name, msg_subscribe_types, msg_publish_type)

    def treat_message(self, msg, topic):
        # if "please" in msg.lower():
        #     new_msg = "NICE"
        # else :
        #     new_msg = "NOT_NICE"


        # Dumb Sentiment analysis performed using nltk library.
        # The result is almost always neutral
        # ToDo: Retrain the pipeline OR use StanfordCoreNLP library

        sid = SentimentIntensityAnalyzer()
        print(msg)
        ss = sid.polarity_scores(msg)

        #Check the sentiment scores in ss[k] and send the tag in k ("pos", "neg" or "neu") with the highest value.
        max_sent_value=0
        for k in ss:
            if k != "compound":
                if ss[k]>max_sent_value:
                    new_msg = k
                    max_sent_value = ss[k]

        print(new_msg)
        self.publish(new_msg)

