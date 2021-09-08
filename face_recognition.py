import numpy as np
import cv2 as cv

haarCascade = cv.CascadeClassifier("haar_face.xml") # reads in the xml haar cascade file


people = ["Orlando", "Titus", "Geoffrey"]


face_recognizer = cv.face.LBPHFaceRecognizer_create()
face_recognizer.read('face_trained.yml')

img = cv.imread("Photos/Orlando/test.jpg")

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Person", gray)

# detect faces in the image
faces_rect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6)

for (x,y,w,h) in faces_rect:
    faces_roi = gray[y:y+h, x:x+h]
    label, confidence = face_recognizer.predict(faces_roi)
    print(confidence)
    print("Label = {} with a confidence of {}".format(label, confidence))

    cv.putText(img, str(people[label]), (20, 20), cv.FONT_HERSHEY_COMPLEX, 1.0, (0,255,0), thickness=2)
    cv.rectangle(img, (x,y), (x+w, y+h), (0,255,0), thickness=2)

cv.imshow("Detected face", img)
cv.waitKey(0)