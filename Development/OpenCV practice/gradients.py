import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Colourful", img)

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Gray", gray)

# Laplacian
# calculates gradient values for the image - i.e. transition from white to black and black to white
lap = cv.Laplacian(gray, cv.CV_64F)
lap = np.uint8(np.absolute(lap)) # np.absolute converts all the integer values of the image to their mod value as pixels cannot be negative. np.uint8() converts the pixel data into an image
cv.imshow("Laplacian", lap)

# Sobel Gradient Magnitude Representation
# computes gradients in x and y direction
sobelx = cv.Sobel(gray, cv.CV_64F, 1, 0) #CV_64F is the data depth.
sobely = cv.Sobel(gray, cv.CV_64F, 0, 1)
combined_sobel = cv.bitwise_or(sobelx, sobely)

cv.imshow("Sobel X", sobelx)
cv.imshow("Sobel Y", sobely)
cv.imshow("Combined Sobel", combined_sobel)

# Canny
# multi-stage. Uses sobel at one stage of its algorithm
canny = cv.Canny(gray, 150, 175)
cv.imshow("Canny", canny)

cv.waitKey(0)