import cv2 as cv

img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image
cv.imshow('Image', img) # displays image 'img' in new window called 'Image Window'

# converting images to greyscale
# grey = cv.cvtColor(img, cv.COLOR_BGR2GRAY) # open cv method which converts image color
# cv.imshow("Greyscale", grey)

# blur
blur = cv.GaussianBlur(img, (1,1), cv.BORDER_DEFAULT)
cv.imshow("Blur", blur)

# Edge Cascade
canny = cv.Canny(blur, 125, 175)
cv.imshow("Canny", canny)

# dilating the image
dilated = cv.dilate(canny, (3,3), iterations=1)
cv.imshow("Dilated", dilated)

# Eroding
eroded = cv.erode(dilated, (3,3), iterations=1) # get the edge cascade back from the dilated images
cv.imshow("Eroded", eroded)

# Resize
resized = cv.resize(img, (750, 750), interpolation=cv.INTER_CUBIC) # resizes and ignores aspect ratio
cv.imshow("Resized", resized)

# Cropping
cropped = img[50:200, 200:300]
cv.imshow("Cropped",cropped)
cv.waitKey(0)