import cv2 as cv
import numpy as np

blank = np.zeros((400,400), dtype='uint8')

rectangle = cv.rectangle(blank.copy(), (30, 30), (370, 370), 255, -1)
circle = cv.circle(blank.copy(), (blank.shape[1]//2, blank.shape[0]//2), 200, 255, -1)

cv.imshow("Rectangle",rectangle)
cv.imshow("Circle", circle)

# bitwise AND - intersecting regions
# common regions to both images set to white and shown. regions that are not common to each image are set to black/not returned
bitwise_and = cv.bitwise_and(rectangle, circle)
cv.imshow("Bitwise AND", bitwise_and)

# bitwise OR - non-intersecting and intersecting regions
# superimposes two images
bitwise_or = cv.bitwise_or(rectangle, circle)
cv.imshow("Bitwise OR", bitwise_or)

# bitwise XOR - non-intersecting regions
bitwise_xor = cv.bitwise_xor(rectangle, circle)
cv.imshow("Bitwise XOR", bitwise_xor)

# bitwise NOT - inverts image
bitwise_not = cv.bitwise_not(circle)
cv.imshow("Bitwise NOT", bitwise_not)


cv.waitKey(0)