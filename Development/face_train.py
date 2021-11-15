import cv2 as cv
import os
import numpy as np
vidcap = cv.VideoCapture(0)
success,image = vidcap.read()
count = 0
while count < 70:
  cv.imwrite("Photos/Orlando/frame%s.png" % count, image)     # save frame as png file
  success, image = vidcap.read()
  print('Read a new frame: ', success)
  count += 1




people = ["Orlando"]

features = []
labels = []
haarCascade = cv.CascadeClassifier("haar_face.xml") # reads in the xml haar cascade file


def create_train():
  for person in people:
    path = os.path.join("Photos", person)
    label = people.index(person)

    for img in os.listdir(path):

      img_path = os.path.join(path, img)
      if img == ".DS_Store":
        pass
      else:
        img_array = cv.imread(img_path)
        gray = cv.cvtColor(img_array, cv.COLOR_BGR2GRAY)

        faces_rect = haarCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

        for (x,y,w,h ) in faces_rect:
          faces_roi = gray[y:y+h, x:x+w] # crops image to just the face in the image, which reduces the chance of noise interfering with the face recognition
          features.append(faces_roi)
          labels.append(label)
  return faces_roi


faces_roi = create_train()
print("Training done ---------------")


features = np.array(features, dtype='object')
labels = np.array(labels)


face_recognizer = cv.face.LBPHFaceRecognizer_create()

# Train the recognizer on the features list and the labels list
face_recognizer.train(features, labels)


face_recognizer.save("face_trained.yml") # saves the trained model
np.save('features.npy', features)
np.save("labels.npy", labels)



vidcap.release()
cv.destroyAllWindows()
