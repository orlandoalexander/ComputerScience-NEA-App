import cv2 as cv
import numpy as np

blank = np.zeros((500,500, 3), dtype="uint8") # creates a blank image - nump.zeros() creates a blank/new array and this is displayed as an image since 'uint8' is the data type of an image



# paint image a certain color
blank[200:300, 300:700] = 0,0,255 # references the pixels and makes them green all green (each pixel has array [0 255 0] to say that each pixel is green
cv.imshow("Green", blank)

# draw rectangle
cv.rectangle(blank,(0,0), (blank.shape[0]//4,blank.shape[1]//2), (0,255,0), thickness=-1)
cv.imshow("Rectangle", blank)

# draw circle
cv.circle(blank, (250,250), 40, (255,0,0), thickness=5)
cv.imshow("Circle", blank)

# draw line
cv.line(blank, (250,0), (100, 250), (255,255,255), thickness=1)
cv.imshow("Line", blank)

# write text
cv.putText(blank, "Hey there", (0,blank.shape[1]-20), cv.FONT_ITALIC, 1.0, (0, 255, 0), thickness=2)
cv.imshow("Text", blank)

cv.waitKey(0)
