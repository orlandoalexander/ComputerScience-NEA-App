import cv2 as cv
import time
import boto3
import string
import random
import mysql.connector
import json
from os.path import join
import threading
import numpy as np

haarCascade = cv.CascadeClassifier("haar_face.xml") # reads in the xml haar cascade file

dbPasswd = "5martB3ll"  # password for AWS RDS database
dbUser = "orlandoalexander"  # username for AWS RDS database
dbHost = "aa8qf9oaqaoklw.cnem9ngqo5zs.eu-west-2.rds.amazonaws.com"  # endpoint for AWS RDS database
dbData = {"passwd": dbPasswd, "user": dbUser,
          "host": dbHost}  # dictionary storing minimum required data to connect to AWS RDS database.
                           # This data is sent to server each time the database is accessed so the
                           # sensitive information is kept secret as it is stored locally
serverBaseURL = "http://nea-server-env.eba-6cwhuc3b.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment
accessKey = "AKIASXUTHDSHXXHEBCEX"
secretKey = "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"

mydb = mysql.connector.connect(host=(dbData["host"]), user=(dbData["user"]), passwd=(dbData["passwd"]),
                               database="ebdb")  # initialises the database using the details sent to API, which can be accessed with the 'request.form()' method
myCursor = mydb.cursor()  # initialises a cursor which allows communication with mydb (MySQL database)


class buttonPressed():
    def __init__(self):
        self.accountID = "yP8cyHE7qu1rlsPA"


    def captureImage(self):
        self.videoCapture = cv.VideoCapture(0)
        counter = 0
        self.blurFactor = []
        self.startTime = time.time()
        while True:
            time.sleep(0.1)
            success, img = self.videoCapture.read()
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            self.faceDetect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=9)  # returns rectangular coordinates of a face.
            # scaleFactor is the percentage by which the image is resized on each iteration of the algorithm to attempt to detect a face in the image, as the face size used in the haar cascade xml is constant, but face sizes in the test image may vary. A small percentage value (i.e. 1.05 which would reduce image size by 5% on each iteration) would mean there is a small step for each resizing, so there is a greater chance of correctly detecting all the faces in the image, although it will be slower than using a larger scale factor
            # minNeighbours specifies how many neighbours each candidate rectangle should have to retain it. In other words, the minimum number of positive rectangles (detect facial features) that need to be adjacent to a positive rectangle in order for it to be considered actually positive. A higher value of minNeighbours will result in less detections but with high quality - somewhere between 3-6

            # for (x, y, w, h) in self.faceDetect:
            #     img = cv.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)

            cv.imwrite("Photos/Visitor/frame%s.png" % counter, img)  # save frame as JPEG file

            self.blurFactor.append((counter, cv.Laplacian(img, cv.CV_64F).var())) # Laplacian operator calculates the gradient change values in an image (i.e. transitions from black to white in greyscale image), so it is used for edge detection. Here, the variance of this operator on each image is returned; if an image contains high variance then there is a wide spread of responses, both edge-like and non-edge like, which is representative of a normal, in-focus image. But if there is very low variance, then there is a tiny spread of responses, indicating there are very little edges in the image, which is typical of a blurry image

            self.time = time.time() - self.startTime
            if (len(self.faceDetect) == 0 and self.time >=3) or self.time >=3:
                break
            else:
                self.num_faceDetect = len(self.faceDetect)
                counter+=1
        if self.num_faceDetect >= 1:
            self.facialRecognition()
        else:
            pass

    def facialRecognition(self):
        self.facialRecognition_image = max(self.blurFactor, key=lambda image: image[1]) # lambda function is an anonymous/nameless function which returns the second element in the tuple for each element in the list, as the second element is the variance of the gradient changes (i.e. number of edges) in each image. Therefore, the max operator is used to find the image with the highest variance of gradient changes as this will be the least blurry image and so most suitable to apply facial recognition to.
        self.img_path = join("Photos/Visitor", "frame"+str(self.facialRecognition_image[0])+".png")
        self.img = cv.imread(self.img_path) # opens the least blurry image of the visitor captured by the doorbell of the visitor - this image is identified by the first element in the tuple 'self.facialRecognition_image'
        print(self.img_path)
        self.gray = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
        self.faceRectangle = haarCascade.detectMultiScale(self.gray, scaleFactor=1.1, minNeighbors=6)
        self.people = []
        with open('data.txt') as jsonFile:
            self.data = json.load(jsonFile)
            for person in self.data[self.accountID]["people"]:
                self.people.append(person)
        self.faceRecognizer = cv.face.LBPHFaceRecognizer_create()
        self.faceRecognizer.read('face_trained.yml')
        for (x, y, w, h) in self.faceRectangle:
            self.faceROI = self.gray[y:y + h, x:x + h]
            self.label, self.confidence = self.faceRecognizer.predict(self.faceROI)
        if self.confidence > 35: # large confidence value means there is a low match as large difference between database and test image
            print(self.confidence)
            print("Unable to identify")
        else:
            print(self.confidence)
            print(self.people[self.label])
            self.thread_updateTraining= threading.Thread(target = self.updateTraining, args = (), daemon = False)

            self.thread_updateTraining.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
            self.create_visitID()



    def updateTraining(self):
        features = np.load('features.npy', allow_pickle=True)
        for person in people:
            path = os.path.join("Photos", person)
            label = people.index(person)

            for img in os.listdir(path):

                img_path = os.path.join(path, img)
                if img == ".DS_Store":
                    pass
                else:
                    img_array = cv.imread(img_path)
                    gray = cv.cvtColor(img_array, cv.COLOR_BGR2GRAY)

                    faces_rect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

                    for (x, y, w, h) in faces_rect:
                        faces_roi = gray[y:y + h,
                                    x:x + w]  # crops image to just the face in the image, which reduces the chance of noise interfering with the face recognition
                        features.append(faces_roi)

    # def uploadAWS_training(self):
    #
    # def uploadAWS_people(self):



    def create_visitID(self):
        # creates a unique faceID for the face captured
        while True: # creates an infinite loop
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
            self.visitID = ''.join(random.choice(chars) for i in range(16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique messageID
            query = "SELECT EXISTS(SELECT * FROM visitorLog WHERE visitID = '%s')" % (self.visitID)  # 'query' variable stores string with MySQL command that is to be executed. The '%s' operator is used to insert variable values into the string.
            myCursor.execute(query)  # the query is executed in the MySQL database which the variable 'myCursor' is connected to
            result = (myCursor.fetchone()[0])  # returns the first result of the query result (accountID), if there is a result to be returned
            if result == 0:
                break
        self.update_visitorLog()


    def update_visitorLog(self):
        query = "INSERT INTO visitorLog(visitID, imageTimestamp, visitorName, accountID) VALUES ('%s','%s','%s','%s')" % (self.visitID, time.time(), self.people[self.label], self.accountID)  # MySQL query to add the data sent with the API to the appropriate columns in the 'knownFaces' table
        myCursor.execute(query)  # executes the query in the MySQL database
        mydb.commit()  # commits the changes to the MySQL database made by the exe
        self.uploadAWS_image()  # calls the method to upload the audio message data to AWS S3


    def uploadAWS_image(self):
        s3 = boto3.client("s3", aws_access_key_id=accessKey, aws_secret_access_key=secretKey)  # initialises a connection to the S3 client on AWS
        s3.upload_file(Filename=self.img_path, Bucket="nea-known-faces", Key=self.visitID)  # uploads the txt file to the S3 bucket called 'nea-audio-messages'. The name of the txt file when it is stored on S3 is the 'messageID' of the audio message which is being stored as a txt file.


    def create_faceID(self):
        # creates a unique faceID for the face captured
        while True: # creates an infinite loop
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
            self.faceID = ''.join(random.choice(chars) for i in range(16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique messageID
            #try:
            query = "SELECT EXISTS(SELECT * FROM knownFaces WHERE faceID = '%s')" % (self.faceID)  # 'query' variable stores string with MySQL command that is to be executed. The '%s' operator is used to insert variable values into the string.
            myCursor.execute(query)  # the query is executed in the MySQL database which the variable 'myCursor' is connected to
            result = (myCursor.fetchone()[0])  # returns the first result of the query result (accountID), if there is a result to be returned
            if result == 0:
                break
        self.update_knowFaces()

    def update_knowFaces(self):
        self.dbData_update = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["faceID"] = self.faceID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        self.dbData_update["accountID"] = self.accountID  # adds the variable 'messageName' to the dictionary 'dbData_update'
        query = "INSERT INTO knownFaces(faceID, accountID) VALUES ('%s','%s')" % (self.faceID, self.accountID)  # MySQL query to add the data sent with the API to the appropriate columns in the 'knownFaces' table
        myCursor.execute(query)  # executes the query in the MySQL database
        mydb.commit()  # commits the changes to the MySQL database made by the exe
        self.uploadAWS_image()  # calls the method to upload the audio message data to AWS S3

        data = {}
        data[self.accountID] = {"people": {}}
        data[self.accountID]["people"] = ["Orlando", "Titus", "Geoffrey"]
        with open('data.txt', 'w') as outfile:
            json.dump(data, outfile)










buttonPressed().captureImage()