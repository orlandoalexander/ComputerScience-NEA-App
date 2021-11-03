import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Original", img)

blank = np.zeros(img.shape[:2], dtype='uint8')

b,g,r = cv.split(img) # split image into color channels

blue = cv.merge([b, blank, blank]) # sets green and red components to black so only displays blue components of the image
green = cv.merge([blank, g, blank])
red = cv.merge([blank, blank, r])

# lighter portions of the color channel represent a high distribution of each color
cv.imshow("Blue only", blue)
cv.imshow("Green only", green)
cv.imshow("Red only", red)


# where the intensity of each color is high, the image is lighter and where the intensity of the colour is lower, the image is darker
cv.imshow("Blue", b)
cv.imshow("Green", g)
cv.imshow("Red", r)

print(img.shape)
print(b.shape) # the color shape is 1 as only showing blue colors
print(g.shape)
print(r.shape)

merged = cv.merge([b,g,r]) # merges individual color channels to make original image
cv.imshow("Merge", merged)

cv.waitKey(0)