import paho.mqtt.client as paho
import time
import broker_config

class Client_Dialog_System():
    def __init__(self,name,msg_publish_type,msg_subscribe_type):
        self.name = name
        self.general_topic = "UoGSocialRobotics/ConversationalAgent/"
        self.msg_publish_type = self.general_topic+msg_publish_type
        self.msg_subscribe_type = self.general_topic+msg_subscribe_type
        self.client = None
        print("Created client %s listening to %s and publishing %s"%(self.name,self.msg_subscribe_type,self.msg_publish_type))

    def _treat_msg(self,msg):
        err_msg = "%s ERR: _treat_msg should have been overwritten in children classes"%self.name
        print(err_msg)
        raise NotImplementedError(err_msg) #not working!?!?

    def _on_message(self,client, userdata, msg):
        print("\n\n%s received message\n--> topic %s\n--> content %s\n"%(self.name,msg.topic,str(msg.payload)))
        self._treat_msg(msg)
        # print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def _on_publish(self,client,user_data,mid):  #keep function signature from paho
        print("%s Just pusblished msg, id = %s"%(self.name,str(mid)))

    def _on_subscribe(self,client, userdata, mid, granted_qos): #keep function signature from paho
        # print("Subscribed: "+str(mid)+" "+str(granted_qos))
        print("%s: subscribed to %s"%(self.name,self.msg_subscribe_type))


    def _connect(self):
        if self.client:
            print("Already connected")
        else:
            self.client = paho.Client()
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe
            self.client.on_message = self._on_message
            self.client.connect(broker_config.ADDRESS, broker_config.PORT)
            # self.client.loop_start()
            print("%s: connexion started"%self.name)

    def _subscribe(self):
        self.client.subscribe(self.msg_subscribe_type, qos=2)
        time.sleep(0.1)

    def _loop_start(self):
        self.client.loop_start()

    def _loop_forever(self):
        self.client.loop_forever()

    def _stop_loop(self):
        self.client.stop_loop()

    def publish(self,message):
        (rc,mid) = self.client.publish(self.msg_publish_type, message, qos=2)
        print(self.msg_publish_type)

    def start_client(self):
        self._connect()
        self._subscribe()
        # self._loop_forever()
