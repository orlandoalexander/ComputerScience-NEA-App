import cv2 as cv

def rescaleFrame(frame, scale=0.2): # scales frame by particular scale value
    height = int(frame.shape[0] * scale)
    width = int(frame.shape[1] * scale)
    dimensions = (width, height)

    return cv.resize(frame, dimensions, interpolation=cv.INTER_AREA) # resizes frame to particular dimension

def changeRes(width, height):
    # live video only
    capture.set(3,width) # 3 references the width of the capture
    capture.set(4, height) # 4 references the height of the capture


img = cv.imread("OpenCV/trump.jpg") # creates a matrix of pixels storing the image
cv.imshow('Image Window', img) # displays image 'img' in new window called 'Image Window'

resizedImage = rescaleFrame(img) # rescales the image
cv.imshow("Resized Image", resizedImage) # displays the resized image

# rescale videos
capture = cv.VideoCapture("OpenCV/fish.mp4") # either takes an integer argument if you want to read in the video input from your webcam or a filepath if you want to read in an existing video
while True:
    isTrue, frame = capture.read() # reads in the video frame by frame, returning the frame and a boolean ('isTrue') which says whether the frame was successfuly read or not
    resizedFrame = rescaleFrame(frame) # rescale each frame
    cv.imshow('Video Window', frame) # displays frame of video in new window called 'Video Window'
    cv.imshow('Resized Video Window', resizedFrame) # displays resized frame of video in new window called 'Resized Video Window'

    if cv.waitKey(1) & 0xFF == ord('q'): # if letter 'd' is pressed - cv.waitKey() returns a 32 Bit integer value. The key input is in ASCII which is an 8 Bit integer value. So you only care about these 8 bits and want all other bits to be 0, which is achieved by using the mask of '0xFF' and using the bitwise operator AND (which is '&' in Python) with the value cv.waitKey()
        break

capture.release()
cv.destroyAllWindows()