from ca_logging import log


class Whiteboard:
    """Singleton class"""
    __instance = None

    @staticmethod
    def getInstance():
        """
        :return: the unique whiteboard object
        """
        if Whiteboard.__instance == None:
            Whiteboard()
        return  Whiteboard.__instance


    def __init__(self, name="whiteboard"):
        """
        This constructor in virtually private.
        :param name: the name of the whiteboard.
        """
        if Whiteboard.__instance != None:
            log.error("Singleton Class: contructor should not be called. Use Whiteboard.getInstance()")
        else:
            Whiteboard.__instance = self
            self.name = name
            log.info("Started whiteboard")
            # dict topics: keys are topics (strings) and values are ClientDialogSystems
            self.topics = dict()
            # dict subscribers: keys are subscribers (ClientDialogSystems) and values are topics (strings)
            self.subscribers = dict()

    def add_elt(self, key, value, d_txt):
        """
        Adds value to a dictionary (given by t_txt) at key
        :param key:
        :param value:
        :param d_txt:
        :return: 1 success / -1 error code
        """
        d = self.subscribers if d_txt == "subscriber" else self.topics
        if key not in d.keys():
            d[key] = list()
        if value in d[key]:
            return -1
        d[key].append(value)
        return 1

    def remove_elt(self, key, value, d_txt):
        """
        Same as add_elt but to remove the value.
        """
        d = self.subscribers if d_txt == "subscriber" else self.topics
        if key in d.keys():
            if value in d[key]:
                d[key].remove(value)
                if len(d[key]) == 0:
                    del d[key]
                return 1
        # print("IN remove_elt in whiboard.py, Could not unsubscribe")
        # print(key)
        # print(value)
        # print(d_txt)
        # print(d)
        return -1

    def add_subscriber_to_topic(self, subscriber, topic):
        return self.add_elt(topic, subscriber, "topic")

    def add_topic_to_subscriber(self, subscriber, topic):
        return self.add_elt(subscriber, topic, "subscriber")

    def remove_subscriber_from_topic(self, subscriber, topic):
        return self.remove_elt(topic, subscriber, "topic")

    def remove_topic_from_subscriber(self, subscriber, topic):
        return self.remove_elt(subscriber, topic, "subscriber")

    def subscribe(self, subscriber, topic):
        v = self.add_subscriber_to_topic(subscriber, topic) + self.add_topic_to_subscriber(subscriber, topic)
        # if v != 2:
        #     log.warning("%s already subscribed to %s." % (subscriber.name, topic))

    def unsubscribe(self, subscriber, topic):
        v = self.remove_subscriber_from_topic(subscriber, topic) + self.remove_topic_from_subscriber(subscriber, topic)
        # if v != 2:
        #     log.warning("ERR, %s not subscribed to %s." % (subscriber.name, topic))

    def get_subscribers(self, topic):
        if topic in self.topics.keys():
            return self.topics[topic]
        else :
            log.warning("Topic %s has no subscribers" % topic)

    def forward_message(self, message, topic):
        """
        forwards message to all subscribers to topic by calling the on_whiteboard_message() method
        """
        subscribers = self.get_subscribers(topic)
        if subscribers is not None:
            for s in subscribers:
                s.on_whiteboard_message(message, topic)

    def publish(self, message, topic):
        self.forward_message(message, topic)


"""Will be used by modules that import whiteboard."""
whiteboard = Whiteboard.getInstance()
