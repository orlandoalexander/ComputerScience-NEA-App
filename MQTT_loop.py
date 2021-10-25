import paho.mqtt.client as mqtt
import requests

serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment
accountID = "jF7sxsG47O0EhGKSRIGKAwSreGFOjfNdHypYAii7u8b="

def on_message_visit(client, userdata, msg):
    visitID = msg.payload.decode()
    data_visitID = {"visitID": str(visitID)}
    res = requests.post(serverBaseURL + "/view_visitorLog", data_visitID).json()
    timestamp = res[0]
    faceID = res[1]
    data_faceID = {"faceID": str(faceID)}
    faceName = requests.post(serverBaseURL + "/view_knownFaces", data_faceID).json()[0]
    if faceName == "":
        update_knownFaces(faceID)
    else:
        print(faceName)

def update_knownFaces(faceID):
    faceName = input("Enter name: ")
    data_knownFaces = {"faceName": faceName, "faceID": faceID}
    res = requests.post(serverBaseURL + "/update_knownFaces", data_knownFaces).text
    print(res)


def on_connect(client, userdata, flags, rc):
    if rc == 0: # if connection is successful
        client.subscribe("visit/{}".format(accountID))
        client.message_callback_add("visit/{}".format(accountID), on_message_visit)
    else:
        # attempts to reconnect
        client.on_connect = on_connect
        client.username_pw_set(username="yrczhohs", password = "qPSwbxPDQHEI")
        client.connect("hairdresser.cloudmqtt.com", 18973)

client = mqtt.Client()
client.username_pw_set(username="yrczhohs", password = "qPSwbxPDQHEI")
client.on_connect = on_connect # creates callback for successful connection with broker
client.connect("hairdresser.cloudmqtt.com", 18973) # parameters for broker web address and port number

client.loop_forever()