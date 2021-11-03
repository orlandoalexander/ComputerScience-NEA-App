import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image
cv.imshow('Image', img) # displays image 'img' in new window called 'Image Window'

# translation
def translate(img, x, y):
    transMat = np.float32([[1,0,x],[0,1,y]]) # x is added to each x coordinate and y is added to each y coordinate
    dimensions = (img.shape[1], img.shape[0]) # width and height of image
    print(img.shape)
    return cv.warpAffine(img, transMat, dimensions)


# rotate
def rotate(img, angle, rotPoint = None):
    (height,width) = img.shape[:2] # height and width are the first two values in shape

    if rotPoint == None:
        rotPoint = (width/2, height/2)

    rotMat = cv.getRotationMatrix2D(rotPoint, angle, 1.0)
    dimensions = (width, height)

    return cv.warpAffine(img, rotMat, dimensions)

# resizing
resized = cv.resize(img, (500, 500), interpolation=cv.INTER_AREA)

# flipping
flip = cv. flip(img, -1)
cv.imshow("Flip", flip)

# cropping
cropped = img[200:400, 300:400]
cv.imshow("Cropped", cropped)


translated = translate(img, -100, 200)
cv.imshow("Translated", translated)

rotated = rotate(img, 180)
cv.imshow("Rotated", rotated)

cv.imshow("Resized", resized)

cv.waitKey(0)