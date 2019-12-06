import movies
from movies import NLU as movies_NLU
from movies import DM as movies_DM
from movies import NLG as movies_NLG
from movies import dum_sentiment_analysis as movies_SA
import food
from food import DM as food_DM
from food import NLG as food_NLG
from food import NLU as food_NLU
from food import heath_diagnostic
import ca_logging as logging
import data_collection
import config

####################################################################################################
##                                          Modules                                               ##
####################################################################################################

class Modules:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique whiteboard object
        """
        if Modules.__instance == None:
            Modules()
        return  Modules.__instance


    def __init__(self):
        """
        This constructor in virtually private.
        :param domain:
        """
        if Modules.__instance != None:
            logging.log.error("Singleton Class: contructor should not be called. Use Modules.getInstance()")
        else:
            Modules.__instance = self
            # self.NLU = None
            # self.DM = None
            # self.SentimentAnalysis = None
            # self.NLG = None
            # self.DataCollector = data_collection.DataCollector
            dataCollector_config = {"module": data_collection.DataCollector, "name": "DataCollector", "subscribes": config.DataCollector_subscribes, "publishes": config.DataCollector_publishes, "ack_msg": config.FIREBASE_KEY_ACK}
            self.modules = list()
            self.modules.append(dataCollector_config)

    def set_domain(self, domain):
        if domain == "movies":
            NLU_config = {"module": movies_NLU.RuleBasedNLU, "name": "NLU", "subscribes": config.NLU_subscribes, "publishes": config.NLU_publishes}
            DM_config = {"module": movies_DM.DM, "name": "DM", "subscribes": config.DM_subscribes, "publishes": config.DM_publishes}
            NLG_config = {"module": movies_NLG.NLG, "name": "NLG", "subscribes": config.NLG_subscribes, "publishes": config.NLG_publishes}
            SA_config = {"module": movies_SA.SentimentAnalysis, "name": "SA",  "subscribes": config.SentimentAnalysis_subscribes, "publishes": config.SentimentAnalysis_publishes}
            self.modules += [NLU_config, DM_config, NLG_config, SA_config]
            logging.log.info("(config.py) Set domain as movies.")
        elif domain == "food":
            NLU_config = {"module": food_NLU.NLU, "name": "NLU", "subscribes": config.NLU_subscribes, "publishes": config.NLU_publishes}
            DM_config = {"module": food_DM.DM, "name": "DM", "subscribes": config.DM_subscribes+[config.MSG_HEALTH_DIAGNOSTIC_OUT], "publishes": config.DM_publishes}
            NLG_config = {"module": food_NLG.NLG, "name": "NLG", "subscribes": config.NLG_subscribes, "publishes": config.NLG_publishes, "tags_explanation_types": config.EXPLANATION_TYPE}
            # SA_config = {"module": movies_SA.SentimentAnalysis, "name": "SA", "subscribes": config.SentimentAnalysis_subscribes, "publishes": config.SentimentAnalysis_publishes}
            HeathDiagnostic_config = {"module": heath_diagnostic.HealthDiagnostic, "name": "FD", "subscribes": config.HealthDiagnostic_subscribes, "publishes": config.HealthDiagnostic_publishes}
            # self.modules += [NLU_config, DM_config, NLG_config, SA_config, HeathDiagnostic_config]
            self.modules += [NLU_config, DM_config, NLG_config, HeathDiagnostic_config]
            logging.log.info("(config.py) Set domain as food.")
        else:
            logging.log.error("No %s domain" % domain)
            exit(0)

modules = Modules.getInstance()
