import cv2 as cv

# reading images
img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image
cv.imshow('Image Window', img) # displays image 'img' in new window called 'Image Window'
cv.waitKey(0) # waits for a specific time delay until a keyboard key is pressed - passing '0' means that it waits for an infinite amount of time

# reading videos
capture = cv.VideoCapture("OpenCV/fish.mp4") # either takes an integer argument if you want to read in the video input from your webcam or a filepath if you want to read in an existing video
while True:
    isTrue, frame = capture.read() # reads in the video frame by frame, returning the frame and a boolean ('isTrue') which says whether the frame was successfuly read or not
    cv.imshow('Video Window', frame) # displays frame of video in new window called 'Video Window'

    if cv.waitKey(1) & 0xFF == ord('d'): # if letter 'd' is pressed - cv.waitKey() returns a 32 Bit integer value. The key input is in ASCII which is an 8 Bit integer value. So you only care about these 8 bits and want all other bits to be 0, which is achieved by using the mask of '0xFF' and using the bitwise operator AND (which is '&' in Python) with the value cv.waitKey()
        break

capture.release()
cv.destroyAllWindows()