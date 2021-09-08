import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/group.JPG") # creates a matrix of pixels storing the image
cv.imshow("Group", img)

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Gray", gray)

haarCascade = cv.CascadeClassifier("haar_face.xml") # reads in the xml haar cascade file

faces_rect = haarCascade.detectMultiScale(gray, scaleFactor=1.1 , minNeighbors=10) # returns rectangular coordinates of a face.
# scaleFactor is the percentage by which the image is resized on each iteration of the algorithm to attempt to detect a face in the image, as the face size used in the haar cascade xml is constant, but face sizes in the test image may vary. A small percentage value (i.e. 1.05 which would reduce image size by 5% on each iteration) would mean there is a small step for each resizing, so there is a greater chance of correctly detecting all the faces in the image, although it will be slower than using a larger scale factor
# minNeighbours specifies how many neighbours each candidate rectangle should have to retain it. In other words, the minimum number of positive rectangles (detect facial features) that need to be adjacent to a positive rectangle in order for it to be considered actually positive. A higher value of minNeighbours will result in less detections but with high quality - somewhere between 3-6

print(len(faces_rect))

for (x,y,w,h) in faces_rect:
    cv.rectangle(img, (x,y), (x+w, y+h), (0,255,0), thickness=2)
cv.imshow("Detected faces", img)

cv.waitKey(0)
