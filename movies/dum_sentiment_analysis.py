import whiteboard_client as wbc
from ca_logging import log
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import helper_functions as helper

class SentimentAnalysis(wbc.WhiteBoardClient,SentimentIntensityAnalyzer):
    def __init__(self, clientid, subscribes, publishes):
        subscribes = helper.append_c_to_elts(subscribes, clientid)
        publishes = publishes + clientid
        wbc.WhiteBoardClient.__init__(self, "SA"+clientid, subscribes, publishes)
        SentimentIntensityAnalyzer.__init__(self)


    def treat_message(self, msg, topic):
        # Dumb Sentiment analysis performed using nltk library.
        # The result is almost always neutral
        # ToDo: Retrain the pipeline OR use StanfordCoreNLP library

        ss = self.polarity_scores(msg)

        ## Check the sentiment scores in ss[k] and send the tag in k ("pos", "neg" or "neu") with the highest value.
        max_sent_value=0
        new_msg = "EMPTY"
        for k in ss:
            if k != "compound":
                if ss[k]>max_sent_value:
                    new_msg = k
                    max_sent_value = ss[k]
        # if "hi" in msg:
        #     new_msg = "NICE"
        # else:
        #     new_msg = "NOT_NICE"

        helper.print_message(self.name,"publishing",new_msg,self.publishes)
        self.publish(new_msg)


if __name__ == "__main__":
    test_sa = SentimentAnalysis("sa_subscribe","sa_publishes","testSA")
    test_sa.treat_message("I like potato","fromclient")
