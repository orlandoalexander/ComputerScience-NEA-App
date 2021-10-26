import paho.mqtt.client as mqtt
import requests
import threading
from cv2 import cv2 as cv



serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment
accountID = "jF7sxsG47O0EhGKSRIGKAwSreGFOjfNdHypYAii7u8b="

def on_message_visit(client, userdata, msg):
    visitID = msg.payload.decode()
    thread_visitorImage = threading.Thread(target = display_visitorImage, args=(str(visitID),), daemon = False) # creates thread to download and display the image of the visitor with visitID. Arguments passed as tuple
    thread_visitorImage.start()
    data_visitID = {"visitID": str(visitID)}
    res = None
    while res == None: # loop until visitID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
        res = requests.post(serverBaseURL + "/view_visitorLog", data_visitID).json()
    faceID = res[1]
    data_faceID = {"faceID": str(faceID)}
    faceName = None
    while faceName == None: # loop until faceID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
        faceName = requests.post(serverBaseURL + "/view_knownFaces", data_faceID).json()[0]
    if faceName == "":
        update_knownFaces(faceID)
    else:
        print(faceName)

def update_knownFaces(faceID):
    faceName = input("Enter name: ")
    data_knownFaces = {"faceName": faceName, "faceID": faceID}
    res = requests.post(serverBaseURL + "/update_knownFaces", data_knownFaces).text

def display_visitorImage(visitID):
    downloadData = {"bucketName": "nea-visitor-log","s3File": visitID}  # creates the dictionary which stores the metadata required to download the pkl file of the image from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
    response = requests.post(serverBaseURL + "/downloadS3", downloadData)
    visitorImage = response.content
    f = open('image.png', 'wb')
    f.write(visitorImage)
    f.close()

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