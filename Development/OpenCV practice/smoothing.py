import cv2 as cv
import numpy as np

img = cv.imread("OpenCV/colourful.jpeg") # creates a matrix of pixels storing the image
cv.imshow("Original", img)

# when you blur an image you use a kernel, which is a window of a certain size that you draw over an image
# the middle pixel of the kernel/window which is drawn over a portion of an image is affected by the surrounding pixels which are inside the kernel


# Averaging
# when using 'averaging' to blur an image, the intensity of the pixel at the centre of the kernel is set to the average of the surrounding pixels

average = cv.blur(img, (3,3))
cv.imshow("Average blur", average)

# Gaussian blur
# sets a weight to each surrounding pixel in the kernel and uses the average of the products of the weights of the surrounding pixels is used to calculate the pixel intensity of the centre pixel. Less, but more natural, blur than averaging
gauss = cv.GaussianBlur(img, (3,3), 0)
cv.imshow("Gaussian blur", gauss)


# Median blur
# very similar to averaging, but instead of finding the average of the surrounding pixels, it finds the median of the surrounding pixels. Effective at reducing noise
median = cv.medianBlur(img, 3) # openCV automatically sets kernel size to 3 by 3 from single integer
cv.imshow("Median blur", median)

# Bilateral
# most effective as it is applies blurring but retains the edges in the image as well
bilateral = cv.bilateralFilter(img, 10, 35, 25) # last property is 'sigma space' and it indicates the maximum distance from the centre of the window where pixels can effect the intensity of the centre pixel
cv.imshow("Bilateral filtering", bilateral)




cv.waitKey(0)