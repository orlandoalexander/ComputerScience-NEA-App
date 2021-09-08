import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Colourful", img)

blank = np.zeros(img.shape[:2], dtype='uint8')

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Gray", gray)

mask = cv.circle(blank, (img.shape[1]//2, img.shape[0]//2), 100, 255, -1)

masked = cv.bitwise_and(img, img, mask=mask)
cv.imshow("Masked", masked)


# Grayscale histogram - calculates how color intensity varies
#gray_hist = cv.calcHist([gray], [0], mask,[256], [0,256]) # channels means number of color types - as grayscale set channels to 0

# plt.figure()
# plt.title("Grayscale histogram")
# plt.xlabel("Bins") # bins are like bars
# plt.ylabel("Num of pixels")
# plt.plot(gray_hist)
# plt.xlim([0,256])
# plt.show()


#Color histogram
plt.figure()
plt.title("Color histogram")
plt.xlabel("Bins") # bins are like bars
plt.ylabel("Num of pixels")
colors = ("b", "g", "r")
for i, col in enumerate(colors):
    color_hist = cv.calcHist([img], [i], mask, [256],[0,256]) # using the mask parameter allows you to create a color histogram for a masked image
    plt.plot(color_hist, color = col)
    plt.xlim([0,256])
plt.show()



cv.waitKey(0)