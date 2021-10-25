import cv2 as cv
import time
import string
import random
import json
from os.path import join
import os
import threading
import numpy as np
import glob
import paho.mqtt.client as mqtt
import shutil
import requests

haarCascade = cv.CascadeClassifier("haar_face.xml") # reads in the xml haar cascade file

if not os.path.isfile("features.npy"):
    featuresNp = np.empty(0, int) # arrays are saved as integers
    np.save('features.npy', featuresNp)
if not os.path.isfile("labels.npy"):
    labelsNp = np.empty(0, int)
    np.save('labels.npy', labelsNp)


serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment


class buttonPressed():
    def __init__(self):
        self.accountID = "yP8cyHE7qu1rlsPA"
        with open('data.json') as jsonFile:
            self.data = json.load(jsonFile)
        self.data.update({self.accountID:{"people":[]}}) # updates json file to create empty parameter to store names of known visitors associated with a specific accountID
        with open('data.json','w') as jsonFile:
            json.dump(self.data, jsonFile)


    def captureImage(self):
        self.videoCapture = cv.VideoCapture(0)
        counter = 0
        imageCaptured = False
        self.blurFactor = []
        while counter < 10:
            success, img = self.videoCapture.read()
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            self.faceDetect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6)  # returns rectangular coordinates of a face.
            # scaleFactor is the percentage by which the image is resized on each iteration of the algorithm to attempt to detect a face in the image, as the face size used in the haar cascade xml is constant, but face sizes in the test image may vary. A small percentage value (i.e. 1.05 which would reduce image size by 5% on each iteration) would mean there is a small step for each resizing, so there is a greater chance of correctly detecting all the faces in the image, although it will be slower than using a larger scale factor
            # minNeighbours specifies how many neighbours each candidate rectangle should have to retain it. In other words, the minimum number of positive rectangles (detect facial features) that need to be adjacent to a positive rectangle in order for it to be considered actually positive. A higher value of minNeighbours will result in less detections but with high quality - somewhere between 3-6
            self.blurFactor.append((counter, cv.Laplacian(img, cv.CV_64F).var())) # Laplacian operator calculates the gradient change values in an image (i.e. transitions from black to white in greyscale image), so it is used for edge detection. Here, the variance of this operator on each image is returned; if an image contains high variance then there is a wide spread of responses, both edge-like and non-edge like, which is representative of a normal, in-focus image. But if there is very low variance, then there is a tiny spread of responses, indicating there are very little edges in the image, which is typical of a blurry image
            self.num_faceDetect = len(self.faceDetect) # finds number of faces detected in image
            if self.num_faceDetect >=1 and self.blurFactor[counter][1] >= 100: # if at least 1 face has been detected and image isn't blurry, save the image
                cv.imwrite("Photos/Visitor/frame%s.png" % counter, img)  # save frame as JPEG file
                imageCaptured = True
            counter+=1
        if imageCaptured == True:
            self.facialRecognition_image = max(self.blurFactor, key=lambda image: image[1]) # lambda function is an anonymous/nameless function which returns the second element in the tuple for each element in the list, as the second element is the variance of the gradient changes (i.e. number of edges) in each image. Therefore, the max operator is used to find the image with the highest variance of gradient changes as this will be the least blurry image and so most suitable to apply facial recognition to.
            self.img_path = ("Photos/Visitor/frame{}.png").format(str(self.facialRecognition_image[0]))
        else:
            success, img = self.videoCapture.read()
            self.img_path = ("Photos/Visitor/frame0.png")
            cv.imwrite(self.img_path, img)  # save frame as JPEG file
        self.create_visitID()
        self.create_faceID()
        self.uploadAWS_image(Bucket="nea-visitor-log", Key = self.visitID)
        if imageCaptured == True: # if a viable image of the visitor has been captured
            self.facialRecognition() # run facial recognition algorithm
        else:
            self.update_visitorLog()
            self.publish_message_visitor("noName")

    def facialRecognition(self):
        self.img = cv.imread(self.img_path) # opens the least blurry image of the visitor captured by the doorbell of the visitor - this image is identified by the first element in the tuple 'self.facialRecognition_image'
        self.gray = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
        self.faceRectangle = haarCascade.detectMultiScale(self.gray, scaleFactor=1.1, minNeighbors=6)
        self.people = []
        with open('data.json') as jsonFile:
            self.data = json.load(jsonFile)
            for person in self.data[self.accountID]["people"]:
                self.people.append(person)
        self.faceRecognizer = cv.face.LBPHFaceRecognizer_create()
        try:
            self.faceRecognizer.read('face_trained.yml')
            for (x, y, w, h) in self.faceRectangle:
                self.faceROI = self.gray[y:y + h,x:x + h]  # crops the image to store only the region containing a detected face, which reduces the chance of noise interfering with the face recognition
                self.label, self.confidence = self.faceRecognizer.predict(self.faceROI)  # runs facial recognition algorithm, returning the name of the person identified and the confidence of this identification
            if self.confidence < 90:
                self.person = self.people[self.label]
                print(self.people[self.label], self.confidence)
                self.update_visitorLog(self.people[self.label])
            else:# large confidence value means there is a low match as large difference between database and test image
                print("Unable to identify", self.confidence)
                self.person = input("Name: ")
                self.update_visitorLog("noName")
                self.publish_message_visitor("noName")
        except:
            self.person = input("Name: ")
            self.update_visitorLog("noName")
            self.publish_message_visitor("noName")
        for img in os.listdir("Photos/Visitor"):
            if not os.path.isdir("Photos/{}".format(self.person)):
                os.mkdir("Photos/{}".format(self.person))
            shutil.move("Photos/Visitor/{}".format(img), "Photos/{}/{}".format(self.person, img))
        if self.person not in self.people:
            self.people.append(self.person)
        self.label = self.people.index(self.person)
        self.data[self.accountID]["people"] = self.people
        with open('data.json', 'w') as f:
            json.dump(self.data, f)
        self.thread_updateTraining = threading.Thread(target=self.updateTraining, args=(), daemon=False)
        self.thread_updateTraining.start()  # starts the thread which will run in pseudo-parallel to the rest of the program

    def updateTraining(self):
        featuresNp = np.load('features.npy',allow_pickle = True) # opens numpy file storing the tagged data for the known faces as list
        labelsNp = np.load("labels.npy", allow_pickle=True)
        features = []
        path = os.path.join("Photos", self.person)
        for img in os.listdir(path): # iterates through the file names within the folder 'path' (i.e. all the photos already stored for the visitor)
            img_path = os.path.join(path, img) # stores full path of each file (image)
            if img == ".DS_Store":
                pass
            else:
                img_array = cv.imread(img_path)
                gray = cv.cvtColor(img_array, cv.COLOR_BGR2GRAY)

                faces_rect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

                for (x, y, w, h) in faces_rect:
                    faces_roi = gray[y:y + h, x:x + w]  # crops image to just the face in the image, which reduces the chance of noise interfering with the face recognition
                    features.append(faces_roi) # update numpy file 'features' which stores the tagged data about the known faces to include the most recently capturd image of the visitor
                    labelsNp = np.append(labelsNp, self.label)
                os.remove(img_path)
        face_recognizer = cv.face.LBPHFaceRecognizer_create()
        featuresNp = np.append(featuresNp, features)
        face_recognizer.train(featuresNp, labelsNp)
        face_recognizer.save("face_trained.yml")  # saves the trained model
        np.save('features.npy', featuresNp)
        np.save("labels.npy", labelsNp)


    # def uploadAWS_training(self):
    #
    #
    # def uploadAWS_people(self):


    def create_visitID(self):
        # creates a unique visitID for each visit
        self.data_vistID = {"field": "visitID"}
        self.visitID = requests.post(serverBaseURL + "/create_ID", self.data_vistID)



    def create_faceID(self):
        # creates a unique faceID for the face captured
        self.data_faceID = {"field": "faceID"}
        self.faceID = requests.post(serverBaseURL + "/create_ID", self.data_faceID)
        print(self.faceID.text)


    def update_visitorLog(self):
        self.data_visitorLog = {"visitID": self.visitID, "imageTimestamp": time.time(), "faceID": self.faceID, "accountID": self.accountID}
        requests.post(serverBaseURL + "/updateVisitorLog", self.data_visitorLog)
        return

    def update_knowFaces(self):
        self.dbData_update = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["faceID"] = self.faceID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        self.dbData_update["accountID"] = self.accountID  # adds the variable 'messageName' to the dictionary 'dbData_update'
        query = "INSERT INTO knownFaces(faceID, accountID) VALUES ('%s','%s')" % (self.faceID, self.accountID)  # MySQL query to add the data sent with the API to the appropriate columns in the 'knownFaces' table
        myCursor.execute(query)  # executes the query in the MySQL database
        mydb.commit()  # commits the changes to the MySQL database made by the exe
        self.uploadAWS_image(Bucket ="nea-known-faces", Key = self.faceID)  # calls the method to upload the audio message data to AWS S3

        data = {}
        data[self.accountID] = {"people": {}}
        print(self.people)
        data[self.accountID]["people"] = ["Orlando", "Titus", "Geoffrey"]
        with open('data.json', 'w') as outfile:
            json.dump(data, outfile)
        for file in glob.glob("Photos/Visitor"):
            os.remove(file) # deletes all the images captured of the visitor

    def uploadAWS_image(self, **kwargs):
        self.uploadData = {"bucketName": kwargs["Bucket"], "s3File": kwargs["Key"]}  # creates the dictionary which stores the metadata required to upload the personalised audio message to AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
        file = {"file": open(self.img_path,"rb")}  # opens the file to be sent using Flask's 'request' method (which contains the byte stream of audio data) and stores the file in a dictionary
        response = requests.post(serverBaseURL + "/uploadS3", files=file, data=self.uploadData)  # sends post request to 'uploadS3' route on AWS server to upload the pkl file storing the data about the audio message to AWS s3 using 'boto3'
        print(response)

    def publish_message_visitor(self, nameStatus):
        client.publish("visitor/{}".format(nameStatus), "{}, {}".format(str(self.accountID),str(self.visitID)))
        return

def on_connect(client, userdata, flags, rc):
    if rc == 0: # if connection is successful
        pass
    else:
        # attempts to reconnect
        client.on_connect = on_connect
        client.username_pw_set(username="yrczhohs", password = "qPSwbxPDQHEI")
        client.connect("hairdresser.cloudmqtt.com", 18973)

client = mqtt.Client()
client.username_pw_set(username="yrczhohs", password = "qPSwbxPDQHEI")
client.on_connect = on_connect # creates callback for successful connection with broker
client.connect("hairdresser.cloudmqtt.com", 18973) # parameters for broker web address and port number

buttonPressed().create_faceID()