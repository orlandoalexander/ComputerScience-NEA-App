import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image


gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # convert image to gray
cv.imshow('Image', gray) # displays image 'gray' in new window called 'Image Window'

# blank
blank = np.zeros(img.shape, dtype="uint8")

# canny
canny = cv.Canny(img, 100, 175) # edges above automatically upper threshold (thresholds are the strength of the edge) and edges below lower threshold automatically discarded. Edges between thresholds are only included if they are connected to edges with intensity above the upper threshold
cv.imshow("Canny edges", canny)

# blur
blur = cv.GaussianBlur(gray, (3,3), cv.BORDER_DEFAULT) # tuple is a kernel which describes the height and width of the matrix which will be used to look at the neighbouring pixels and average them. A larger kernel means more pixels are averaged together.
cv.imshow("Blurred", blur)

# threshold
ret, thresh = cv.threshold(gray, 100, 255, cv.THRESH_BINARY) #thresholding means that the image is binarised - if the intensity of a pixel is below 100, then set to black, and if above 255 then set to white
cv.imshow("Threshold", thresh)

# contours
contours, hierarchies = cv.findContours(canny, cv.RETR_LIST, cv.CHAIN_APPROX_NONE) # looks at edges found in image (canny) and returns contours which is a python list of all the contours in the image and the hierarchachal representation of the contours. cv.RETR_LIST retruns all the contours in the image. cv.CHAIN_APPROX_NONE returns all the contours (the other option might be cv.RETR_SIMPLE which would simplify the contours - i.e. for a line only the contours at each end of the line would be returned
print(len(contours))

# visualize contours
cv.drawContours(blank, contours, -1, (0,0,255), 1) # -1 says that you want all the contours to be drawn
cv.imshow("Draw contours",blank) # draws the edges of the contours found using the threshold function

cv.waitKey(0)