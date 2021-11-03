import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Original", img)

blank = np.zeros(img.shape[:2], dtype='uint8') # size of mask must be same size as image that its is being masked with
cv.imshow("Blank", blank)

circle = cv.circle(blank.copy(), (img.shape[1]//2, img.shape[0]//2),100, 255, -1)
#cv.imshow("Mask", mask)

rectangle = cv.rectangle(blank.copy(), (100, 100), (500, 500), 255, -1)

weird_shape = cv.bitwise_and(circle, rectangle)
cv.imshow("Weird shape", weird_shape)

maskedImage = cv.bitwise_and(img, img, mask=weird_shape)
cv.imshow("Wierd shape Masked Image", maskedImage)


cv.waitKey(0)