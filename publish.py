import paho.mqtt.client as mqtt # import paho-mqtt-client module

def on_message(client, userdata, msg): # function called when a message is received
    messageData = msg.payload.decode() # decode the message data received (‘msg’ variabvel) into utf-8 and assign this message to variable ‘messageData’


def on_connect(client, userdata, flags, rc): # function called when the client connects to the broker
    if rc == 0: # if connection is successful
        client.publish("myTopic", "myMessage")# publishes message ‘myMessage’ to ‘myTopic’
        client.subscribe("subscribeTopic") # subscribe to the topic ‘subscribeTopic’ so that messages published to this topic are received
        client.message_callback_add("subscribeTopic", on_message)
    else:
        # if connection is unsuccessful, attempts to reconnect
        client = mqtt.Client()
        client.username_pw_set(username="myUsername", password="myPassword")
        client.on_connect = on_connect

client = mqtt.Client() # instantiate instance of the Client class
client.username_pw_set(username="myUsername", password="myPassword") # details to connect to MQTT broker
client.on_connect = on_connect # create callback function which is run when the client connects to the broker

client.connect("hairdresser.cloudmqtt.com", 18973) # attempt to connect to the MQTT broker
client.loop_forever() # loops the above code forever so messages published to ‘myTopic’ are received instantly


# serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"
# import wave
# import pickle
# import requests
#
# downloadData = {"bucketName": "nea-audio-messages",
#                                      "s3File": "GD1j9cF9EGYVpw18"}  # creates the dictionary which stores the metadata required to download the pkl file of the personalised audio message from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
# response = requests.post(serverBaseURL + "/downloadS3", downloadData)
# audioData = response.content
# audioData = pickle.loads(response.content)  # unpickles the byte string
#
# messageFile = wave.open("test.wav", "wb")
# messageFile.setnchannels(1)  # change to 1 for audio stream module
# messageFile.setsampwidth(2)
# messageFile.setframerate(8000)  # change to 8000 for audio stream module
# messageFile.writeframes(b''.join(audioData))
# messageFile.close()

