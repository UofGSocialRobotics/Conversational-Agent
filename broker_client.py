import paho.mqtt.client as paho
import helper_functions as helper
import broker_config as config

class Client_Dialog_System():
    def __init__(self,name,msg_subscribe_type=None,msg_publish_type=None):
        self.name = name
        self.msg_publish_type = msg_publish_type if msg_publish_type else None
        self.msg_subscribe_type = msg_subscribe_type if msg_subscribe_type else None
        self.client = None
        print("%s: init"%(self.name))

    def _treat_msg(self,msg):
        err_msg = "%s ERR: _treat_msg should have been overwritten in children classes"%self.name
        print(err_msg)
        raise NotImplementedError(err_msg) #not working!?!?

    def _on_message(self,client, userdata, msg):
        helper.print_message(self.name,"received",str(msg.payload),msg.topic)
        self._treat_msg(msg)
        # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def _on_publish(self,client,user_data,mid):  #keep function signature from paho
        print("%s pusblished msg, id = %s"%(self.name,str(mid)))

    def _on_subscribe(self,client, userdata, mid, granted_qos): #keep function signature from paho
        # print("Subscribed: "+str(mid)+" "+str(granted_qos))
        print("%s: subscribed, %s, %s"%(self.name,str(mid),str(granted_qos)))


    def _connect(self):
        if self.client:
            print("Already connected")
        else:
            self.client = paho.Client()
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            self.client.on_message = self._on_message
            self.client.connect(config.ADDRESS, config.PORT)
            # self.client.loop_start()
            print("%s: connexion started"%self.name)

    def _subscribe(self,topic=None):
        if topic == None:
            if self.msg_subscribe_type == None :
                print("%s ERR: no topic provided to subscribe to topic"%(self.name))
                return
            topic = self.msg_subscribe_type
        print("%s: suscribing to %s"%(self.name,topic))
        self.client.subscribe(topic, qos=2)


    def _loop_start(self):
        self.client.loop_start()

    def _loop_forever(self):
        self.client.loop_forever()

    def _stop_loop(self):
        self.client.stop_loop()

    def publish(self,message,topic=None):
        print("%s: in publish"%self.name)
        if topic == None :
            if self.msg_publish_type == None:
                print("%s ERR: no topic provided to publish message \"%s\""%(self.name,message))
                return
            topic = self.msg_publish_type
        helper.print_message(self.name,"publishing",message,topic)
        (rc,mid) = self.client.publish(topic, message, qos=2)

    def start_client(self):
        self._connect()
        self._subscribe()
        # self._loop_forever()

    def start_client_and_loop_forver(self):
        self._connect()
        self._subscribe()
        self._loop_forever()
