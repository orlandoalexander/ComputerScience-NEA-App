import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image

# BGR to Grayscale

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Grayscale", gray)

# BGR to HSV - Hue Saturation Value
HSV = cv.cvtColor(img, cv.COLOR_BGR2HSV)
cv.imshow("HSV", HSV)

# BGR to LAB
Lab = cv.cvtColor(img, cv.COLOR_BGR2Lab)
cv.imshow("Lab", Lab)

# BGR to RGB
RGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
cv.imshow("RGB", RGB)

# HSV to BGR
hsv_bgr = cv.cvtColor(HSV, cv.COLOR_HSV2BGR)
cv.imshow("hsv_bgr", hsv_bgr)


cv.waitKey(0)