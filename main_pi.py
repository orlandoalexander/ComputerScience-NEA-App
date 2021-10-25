from cv2 import cv2 as cv
import time
import json
import boto3
import os
import threading
import numpy as np
import glob
import paho.mqtt.client as mqtt
import shutil
import requests
from cryptography.fernet import Fernet


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
        self.accountID = "jF7sxsG47O0EhGKSRIGKAwSreGFOjfNdHypYAii7u8b="
        with open('data.json') as jsonFile:
            self.data = json.load(jsonFile)
        if self.accountID not in self.data: # if data for account not yet stored
            self.data.update({self.accountID:{"faceIDs":[]}}) # updates json file to create empty parameter to store names of known visitors associated with a specific accountID
            with open('data.json','w') as jsonFile:
                json.dump(self.data, jsonFile)


    def captureImage(self):
        self.videoCapture = cv.VideoCapture(0)
        counter = 0
        flag = 0
        imageCaptured = False
        self.blurFactor = []
        while flag < 10:
            success, img = self.videoCapture.read()

            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            faceDetect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)  # returns rectangular coordinates of a face.
            # scaleFactor is the percentage by which the image is resized on each iteration of the algorithm to attempt to detect a face in the image, as the face size used in the haar cascade xml is constant, but face sizes in the test image may vary. A small percentage value (i.e. 1.05 which would reduce image size by 5% on each iteration) would mean there is a small step for each resizing, so there is a greater chance of correctly detecting all the faces in the image, although it will be slower than using a larger scale factor
            # minNeighbours specifies how many neighbours each candidate rectangle should have to retain it. In other words, the minimum number of positive rectangles (detect facial features) that need to be adjacent to a positive rectangle in order for it to be considered actually positive. A higher value of minNeighbours will result in less detections but with high quality - somewhere between 3-6
            blurFactor = cv.Laplacian(img, cv.CV_64F).var()# Laplacian operator calculates the gradient change values in an image (i.e. transitions from black to white in greyscale image), so it is used for edge detection. Here, the variance of this operator on each image is returned; if an image contains high variance then there is a wide spread of responses, both edge-like and non-edge like, which is representative of a normal, in-focus image. But if there is very low variance, then there is a tiny spread of responses, indicating there are very little edges in the image, which is typical of a blurry image
            num_faceDetect = len(faceDetect) # finds number of faces detected in image
            if num_faceDetect >=1 and blurFactor >= 100 and flag > 0: # if at least 1 face has been detected and image isn't blurry, save the image
                cv.imwrite("Photos/Visitor/frame%s.png" % counter, img)  # save frame as JPEG file
                self.blurFactor.append((counter, blurFactor))
                imageCaptured = True
                counter +=1
            flag +=1
        if imageCaptured == True:
            self.facialRecognition_image = max(self.blurFactor, key=lambda image: image[1]) # lambda function is an anonymous/nameless function which returns the second element in the tuple for each element in the list, as the second element is the variance of the gradient changes (i.e. number of edges) in each image. Therefore, the max operator is used to find the image with the highest variance of gradient changes as this will be the least blurry image and so most suitable to apply facial recognition to.
            self.img_path = ("Photos/Visitor/frame{}.png").format(str(self.facialRecognition_image[0]))
        else:
            success, img = self.videoCapture.read()
            self.img_path = ("Photos/Visitor/frame0.png")
            cv.imwrite(self.img_path, img)  # save frame as JPEG file
        self.visitID = self.create_visitID()
        self.uploadAWS_image(Bucket="nea-visitor-log", Key = self.visitID)
        if imageCaptured == True: # if a viable image of the visitor has been captured
            self.publish_message_visitor()
            self.facialRecognition() # run facial recognition algorithm
        else:
            self.publish_message_visitor()

    def facialRecognition(self):
        self.img = cv.imread(self.img_path) # opens the least blurry image of the visitor captured by the doorbell of the visitor - this image is identified by the first element in the tuple 'self.facialRecognition_image'
        self.gray = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
        self.faceRectangle = haarCascade.detectMultiScale(self.gray, scaleFactor=1.1, minNeighbors=4)

        self.faceIDs = []
        with open('data.json') as jsonFile:
            self.data = json.load(jsonFile)
            for faceID in self.data[self.accountID]["faceIDs"]:
                self.faceIDs.append(faceID)
        try: # try except needed as block of code will break if no previous file called 'face_trained.yml' (i.e. first time running the program)
            self.faceRecognizer = cv.face.LBPHFaceRecognizer_create()
            self.faceRecognizer.read('face_trained.yml')
            for (x, y, w, h) in self.faceRectangle:
                self.faceROI = self.gray[y:y + h,x:x + h]  # crops the image to store only the region containing a detected face, which reduces the chance of noise interfering with the face recognition
                self.label, self.confidence = self.faceRecognizer.predict(self.faceROI)  # runs facial recognition algorithm, returning the name of the faceID identified and the confidence of this identification
            if self.confidence < 90:
                self.faceID = self.faceIDs[self.label]
                print(self.faceID, self.confidence)
            else:
                self.faceID = self.create_faceID()
        except:
            self.faceID = self.create_faceID()
        self.publish_message_visitor()
        self.update_visitorLog()
        for img in os.listdir("Photos/Visitor"):
            if not os.path.isdir("Photos/{}".format(self.faceID)):
                os.mkdir("Photos/{}".format(self.faceID))
            shutil.move("Photos/Visitor/{}".format(img), "Photos/{}/{}".format(self.faceID, img))
        if self.faceID not in self.faceIDs:
            self.faceIDs.append(self.faceID)
        self.label = self.faceIDs.index(self.faceID)
        self.data[self.accountID]["faceIDs"] = self.faceIDs
        with open('data.json', 'w') as f:
            json.dump(self.data, f)
        self.thread_updateTraining = threading.Thread(target=self.updateTraining, args=(), daemon=False)
        self.thread_updateTraining.start()  # starts the thread which will run in pseudo-parallel to the rest of the program

    def updateTraining(self):
        featuresNp = np.load('features.npy',allow_pickle = True) # opens numpy file storing the tagged data for the known faces as list
        labelsNp = np.load("labels.npy", allow_pickle=True)
        features = []
        path = os.path.join("Photos", self.faceID)
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
        os.rmdir(path)



    def create_visitID(self):
        # creates a unique visitID for each visit
        self.data_vistID = {"field": "visitID"}
        visitID = requests.post(serverBaseURL + "/create_ID", self.data_vistID).text
        return visitID


    def create_faceID(self):
        # creates a unique faceID for the face captured
        self.data_faceID = {"field": "faceID"}
        faceID = requests.post(serverBaseURL + "/create_ID", self.data_faceID).text
        return faceID


    def update_visitorLog(self):
        self.data_visitorLog = {"visitID": self.visitID, "imageTimestamp": time.time(), "faceID": self.faceID, "accountID": self.accountID}
        requests.post(serverBaseURL + "/update_visitorLog", self.data_visitorLog)
        return

    def uploadAWS_image(self, **kwargs):
        fernet = Fernet(self.accountID.encode()) # instantiate Fernet class with users accountID as the key
        self.data_S3Key = {"accountID": self.accountID}
        hashedKeys = requests.post(serverBaseURL + "/get_S3Key", self.data_S3Key).json() # returns json object with encoded keys
        accessKey = fernet.decrypt(hashedKeys["accessKey_encoded"].encode()).decode() # encoded byte string returned so must use 'decode()' to decode it
        secretKey = fernet.decrypt(hashedKeys["secretKey_encoded"].encode()).decode()
        s3 = boto3.client("s3", aws_access_key_id=accessKey, aws_secret_access_key=secretKey)  # initialises a connection to the S3 client on AWS using the 'accessKey' and 'secretKey' sent to the API
        s3.upload_file(Filename=self.img_path, Bucket=kwargs["Bucket"], Key=kwargs["Key"])  # uploads the txt file to the S3 bucket called 'nea-audio-messages'. The name of the txt file when it is stored on S3 is the 'messageID' of the audio message which is being stored as a txt file.


    def publish_message_visitor(self):
        client.publish("visit/{}".format(str(self.accountID)), "{}".format(str(self.visitID)))
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

buttonPressed().captureImage()