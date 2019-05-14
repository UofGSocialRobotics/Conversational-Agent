

class LocalBrocker:
    def __init__(self, name="loacl broker"):
        self.name = name
        print("Started local_broker")
        # dict topics: keys are topics (strings) and values are ClientDialogSystems
        self.topics = dict()
        # dict subscribers: keys are subscribers (ClientDialogSystems) and values are topics (strings)
        self.subscribers = dict()

    def add_elt(self, key, value, d_txt):
        d = self.subscribers if d_txt == "subscriber" else self.topics
        if key not in d.keys():
            d[key] = list()
        if value in d[key]:
            return -1
        d[key].append(value)
        return 1

    def remove_elt(self, key, value, d_txt):
        d = self.subscribers if d_txt == "subscriber" else self.topics
        if key in d.keys():
            if value in d[key]:
                d[key].remove(value)
                if len(d[key]) == 0:
                    del d[key]
                return 1
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
        if v != 2:
            print("ERR, %s already subscribed to %s." % (subscriber.name, topic))

    def unsubscribe(self, subscriber, topic):
        v = self.remove_subscriber_from_topic(subscriber, topic) + self.remove_topic_from_subscriber(subscriber, topic)
        if v != 2:
            print("ERR, %s not subscribed to %s." % (subscriber.name, topic))

    def get_subscribers(self, topic):
        if topic in self.topics.keys():
            return self.topics[topic]
        else :
            print("Topic %s has no subscribers"%topic)

    def forward_message(self, message, topic):
        print(self.name+" in forward_message")
        subscribers = self.get_subscribers(topic)
        if subscribers is not None:
            for s in subscribers:
                print(s)
                s.on_local_message(message, topic)

    def publish(self, message, topic):
        self.forward_message(message, topic)
