import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Colourful", img)

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Gray", gray)

# Simple thresholding - user manually enters threshold value
threshold, thresh = cv.threshold(gray, 150, 255, cv.THRESH_BINARY) # looks at each pixel in the image and if it is above the value of 150 in intensity it is set to 255 so the image is binarized (i.e. high intensity colours set to white and low intensity colours set to black)
# threshold is the threshold value (150) and thresh is the new binarized immage
cv.imshow("Simple Thresholded", thresh)

# threshold, thresh_inv = cv.threshold(gray, 150, 255, cv.THRESH_BINARY_INV) # looks at each pixel in the image and if it is above the value of 150 in intensity it is set to 255 so the image is binarized (i.e. high intensity colours set to white and low intensity colours set to black)
# # white changed to black and black changed to white
# cv.imshow("Simple Thresholded Inverse", thresh_inv)


# Adaptive thresholding - computer automatically finds optimal threshold value
adaptive_thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C,cv.THRESH_BINARY, 11, 7) # threshold method finds mean of neighbouring pixels to select threshold value. Blocksize is the kernel used to find the mean intensity of neighbouring pixels to determine threshold value
# cv.ADAPTIVE_THRESH_GAUSSIAN_C can be used instead of cv.ADAPTIVE_THRESH_MEAN_C in some cases - GAUSSIAN gives a weight to surrounding pixels when calculating intensity values of these pixels, so that pixels closer to the central pixel are given a greater weighted average intensity value
cv.imshow("Adaptive threshold", adaptive_thresh)



cv.waitKey(0)


