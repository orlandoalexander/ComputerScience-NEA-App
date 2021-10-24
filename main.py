from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.taptargetview import MDTapTargetView
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from os.path import join
import os
import re
import random
import string
import requests
import hashlib
import threading
import time
import math
import wave
import importlib
import sys
from audiostream import get_input
import pickle

#
# import pyaudio
# import wave
#
# chunk = 1024  # Record in chunks of 1024 samples
# sample_format = pyaudio.paInt16  # 16 bits per sample
# channels = 2
# fs = 44100  # Record at 44100 samples per second
# seconds = 3
# filename = "output.wav"
#
# p = pyaudio.PyAudio()  # Create an interface to PortAudio
#
# print('Recording')
#
# stream = p.open(format=sample_format,
#                 channels=channels,
#                 rate=fs,
#                 frames_per_buffer=chunk,
#                 input=True)
#
# frames = []  # Initialize array to store frames
#
# # Store data in chunks for 3 seconds
# for i in range(0, int(fs / chunk * seconds)):
#     data = stream.read(chunk)
#     frames.append(data)
#
# # Stop and close the stream
# stream.stop_stream()
# stream.close()
# # Terminate the PortAudio interface
# p.terminate()
# print('Finished recording')
#
# with open ("sampleAudio.pkl", "wb") as file:
#     pickle.dump(frames, file)
#     file.close()
#
# with open ("sampleAudio.pkl", "rb") as file:
#     frames = pickle.load(file)

# wf = wave.open("test.wav", 'wb')
# wf.setnchannels(2)
# wf.setsampwidth(2)
# wf.setframerate(44100)
# wf.writeframes(b''.join(frames))
# wf.close()


Window.size = (440, 1330)


serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment


class WindowManager(ScreenManager):
    # 'WindowManager' class used for transitions between GUI windows
    pass



class Launch(Screen, MDApp):
# 'Launch' class serves to coordinate the correct launch screen for the mobile app depending on the current status of the app

    def __init__(self, **kw):
        super().__init__(**kw)
        global jsonFilename, jsonStore
        jsonFilename = join(MDApp.get_running_app().user_data_dir,
                            "jsonStore.json")# if file name already exists, it is assigned to 'self.filename'. If filename doesn't already exist, file is created locally on the mobile phone
        # the 'join' class is used to create a single path name to the new file "jsonStore.json"

        jsonStore = JsonStore(
            jsonFilename)# wraps the filename as a json object to store data locally on the mobile phone
        if not jsonStore.exists("localData"):
            jsonStore.put("localData", initialUse="True", loggedIn="False", accountID = "")
        self.initialUse = jsonStore.get("localData")["initialUse"]# variable which indicates that the app is running for the first time on the user's mobile

        self.loggedIn = jsonStore.get("localData")["loggedIn"]
        Clock.schedule_once(self.finishInitialising)# Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisationas the instantiation results in 1 of 3 methods (Homepage(), signIn() or signUp()) being called, each of which requires access to Kivy ids to create the GUI


    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation

        if self.loggedIn == "True":
            self.manager.transition = NoTransition()
            self.manager.current = "Homepage"  # if the user is already logged in, then class 'Homepage' is called to allow the user to navigate the app

        elif self.initialUse == "True":
            self.manager.transition = NoTransition()
            self.manager.current = "SignIn"
        else:
            self.manager.transition = NoTransition()
            self.manager.current = "SignUp"


class SignUp(Screen, MDApp):
    # 'SignUp' class allows user to create an account

    def create_userAccount(self):
        # method called when user taps the Sign Up button
        self.firstName_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.surname_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.email_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.password_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.initialUse = jsonStore.get("localData")["initialUse"]
        if self.ids.firstName.text == "":  # if no data is inputted...
            self.ids.firstName_error.opacity = 1  # ...then an error message is displayed
        else:
            self.firstName = self.ids.firstName.text  # inputted first name assigned to a variable
            self.ids.firstName_error.opacity = 0  # error message removed
            self.firstName_ok = True  # variable which indicates that a valid value has been inputted by the user
        if self.ids.surname.text == "":  # if no data is inputted...
            self.ids.surname_error.opacity = 1  # ...then an error message is displayed
        else:
            self.surname = self.ids.surname.text  # inputted surname assigned to a variable
            self.ids.surname_error.opacity = 0  # error message removed
            self.surname_ok = True  # variable which indicates that a valid value has been inputted by the user
        if self.ids.email.text == "":  # if no data is inputted...
            self.ids.email_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.email_error_invalid.opacity = 0  # invalid email error message is removed
        else:
            email = self.ids.email.text
            if re.search("[@]", email) and re.search("[.]", email):  # checks that inputted email contains '@' symbol and '.' to verify the email address as a valid email format
                self.email = self.ids.email.text  # inputted email assigned to a variable
                self.ids.email_error_blank.opacity = 0  # error message removed
                self.ids.email_error_invalid.opacity = 0  # invalid email error message removed
                self.email_ok = True  # variable which indicates that a valid value has been inputted by the user
            else:
                self.ids.email_error_blank.opacity = 0  # blank data error message removed
                self.ids.email_error_invalid.opacity = 1  # invalid email error message displayed
        if self.ids.password.text == "":  # if no data is inputted...
            self.ids.password_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
        else:
            password = self.ids.password.text
            if (len(password) >= 8) and re.search("[a-z]", password) and re.search("[A-Z]", password) and re.search(
                    "[0-9]", password) and re.search("[_@$!£#*%]", password):
                # checks that inputted password is at least 8 characters and contains at least 1 lowercase character,
                # 1 uppercase character, 1 digit and 1 special character" regular expression module used to search
                # the inputted password for a variety of different requirements
                self.password = self.ids.password.text  # inputted password assigned to a variable
                self.hashedPassword = (hashlib.new("sha3_256",
                                                   self.password.encode())).hexdigest()  # creates a hash of the user's password so that it is encrypted when it is stored on the database so more secure
                # the hashing algorithm SHA3-256 is used by the 'hashlib' module to encrypt the UTF-8 encoded version
                # of the password (the method 'encode()' UTF-8 encodes the plaintext password) the method 'hexdigest()'
                # returns the hex value of the hashed password that has been created
                self.ids.password_error_blank.opacity = 0  # error message removed
                self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
                self.password_ok = True  # variable which indicates that a valid value has been inputted by the user
                if self.firstName_ok and self.surname_ok and self.email_ok and self.password_ok:  # checks if all the data values have been inputted and are valid
                    self.create_accountID()  # method called to create a unique accountID for the user
                else:
                    pass
            else:
                self.ids.password_error_blank.opacity = 0  # blank data error message removed
                self.ids.password_error_invalid.opacity = 1  # invalid password error message displayed

    def create_accountID(self):
        # creates a unique accountID for the user
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
        self.accountID = ''.join(random.choice(chars) for i in range(16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique accountID
        self.updateUsers()

    def updateUsers(self):
        # add user's details to 'users' tabel in AWS RDS database
        self.dbData_update = dbData # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData'
        self.dbData_update["firstName"] = self.firstName  # adds the variable 'firstName' to the dictionary 'dbData'
        self.dbData_update["surname"] = self.surname  # adds the variable 'surname' to the dictionary 'dbData'
        self.dbData_update["email"] = self.email  # adds the variable 'email' to the dictionary 'dbData'
        self.dbData_update["password"] = self.hashedPassword  # adds the variable 'hashPassword' to the dictionary 'dbData'
        response = requests.post(serverBaseURL + "/verifyAccount", self.dbData_update) # sends post request to 'verifyAccount' route on AWS server to check whether the email address inputted is already associated with an account
        if response.text == "exists": # if the inputted email address is already associated with an account
            self.ids.snackbar.text = "Account with this email address already exists. Login instead"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.ids.snackbar.font_size = 24
            self.openSnackbar()  # calls the method which creates the snackbar animation
            self.thread_dismissSnackbar = threading.Thread(target=self.dismissSnackbar, args=(),daemon=False)  # initialises an instance of the 'threading.Thread()' method
            self.thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
        else:
            response = requests.post(serverBaseURL + "/updateUsers", self.dbData_update)  # sends post request to 'updateUsers' route on AWS server with user's inputted data to be stored in the database
            if response.text == "error": # if an error occurs when adding the user's data into the 'users' table
                self.ids.snackbar.text = "Error creating account. Please try again later" # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
                self.ids.snackbar.font_size = 30
                self.openSnackbar() # calls the method which creates the snackbar animation
                self.thread_dismissSnackbar = threading.Thread(target=self.dismissSnackbar, args=(), daemon=False)  # initialises an instance of the 'threading.Thread()' method
                self.thread_dismissSnackbar.start() # starts the thread which will run in pseudo-parallel to the rest of the program
            else:
                jsonStore.put("localData", initialUse=self.initialUse,
                                   loggedIn="True", accountID = self.accountID) # updates json object to reflect that user has successfully created an account
                if self.initialUse == "True":  # if the app is running for the first time on the user's mobile
                    self.manager.transition = NoTransition()  # creates a cut transition type
                    self.manager.current = "Homepage"  # switches to 'Homepage' GUI
                    self.manager.current.__init__()

    def openSnackbar(self):
        # method which controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0.095},
                              d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # method which controls the closing animation of the snackbar
        time.sleep(3.5)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0},
                              d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation


class SignIn(Screen, MDApp):
    # 'SignIn' class allows users to log into their account

    def signIn(self):
        # method called when user taps the Sign In button
        self.email_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.password_ok = False  # variable which indicates that a valid value has been inputted by the user
        self.initialUse = jsonStore.get("localData")["initialUse"]
        if self.ids.email.text == "":  # if no data is inputted...
            self.ids.email_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.email_error_invalid.opacity = 0  # invalid email error message is removed
        else:
            self.email = self.ids.email.text  # inputted email assigned to a variable
            self.ids.email_error_blank.opacity = 0  # error message removed
            self.email_ok = True
        if self.ids.password.text == "":  # if no data is inputted...
            self.ids.password_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
        else:
            self.password = self.ids.password.text  # inputted password assigned to a variable
            self.hashedPassword = (hashlib.new("sha3_256", self.password.encode())).hexdigest()  # creates a hash of the user's password so that it can be compared to the hashed version stored on the database
            # the hashing algorithm SHA3-256 is used by the 'hashlib' module to encrypt the UTF-8 encoded version of
            # the password (the method 'encode()' UTF-8 encodes the plaintext password) the method 'hexdigest()'
            # returns the hex value of the hashed password that has been created
            self.ids.password_error_invalid.opacity = 0  # error message removed
            self.password_ok = True  # variable which indicates that a valid value has been inputted by the user
            if self.email_ok and self.password_ok:  # checks if all the data values have been inputted and are valid
                self.verifyUser()

    def verifyUser(self):
        # verifies the email and password entered by the user
        self.dbData_verify = dbData # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_verify["email"] = self.email # adds the variable 'email' to the dictionary 'dbData'
        self.dbData_verify["password"] = self.hashedPassword # adds the variable 'password' to the dictionary 'dbData'
        response = requests.post(serverBaseURL + "/verifyUser", self.dbData_verify) # sends a post request to the 'verifyUser' route of the AWS server to validate the details (email and password) entered by the user
        if response.text == "none": # if the details inputted by the user don't match an existing account
            self.openSnackbar() # calls the method which creates the snackbar animation
            self.thread_dismissSnackbar = threading.Thread(target=self.dismissSnackbar, args=(), daemon=False)  # initialises an instance of the 'threading.Thread()' method
            self.thread_dismissSnackbar.start() # starts the thread which will run in pseudo-parallel to the rest of the program
        else:
            self.accountID = response.text # if the user inputs details which match an account stored in the MySQL database, their unique accountID is returned
            jsonStore.put("localData", initialUse=self.initialUse, loggedIn="True", accountID = self.accountID)  # updates json object to reflect that user has successfully signed in
            if self.initialUse == "True": # if the app is running for the first time on the user's mobile
                self.manager.transition = NoTransition()  # creates a cut transition type
                self.manager.current = "Homepage"  # switches to 'Homepage' GUI
                self.manager.current_screen.darkenImage()

    def openSnackbar(self):
        # method which controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0.1},
                              d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # method which controls the closing animation of the snackbar
        time.sleep(3.5)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0},
                              d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation


class Homepage(Screen, MDApp):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.initialUse = jsonStore.get("localData")["initialUse"]

    def darkenImage(self):
        # method which increases the opacity of an image
        self.thread_lightenImage = threading.Thread(target=self.lightenImage, args=(),
                                                    daemon=False)  # initialises an instance of the 'threading.Thread()' method
        self.thread_lightenImage.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
        animation = Animation(opacity=0.7,
                              d=0.4)  # automatic animation which gradually increases the opacity of the red circle image from 0 to 0.7
        animation.start(self.redCircle)  # starts the animation of the red circle image

    def lightenImage(self):
        # method which decreases the opacity of an image
        time.sleep(1)  # delay before image is lightened
        animation = Animation(opacity=0,
                              d=0.4)  # automatic animation which gradually reduce the opacity of red circle from 0.7 to 0
        animation.start(self.redCircle)  # starts the animation of the red circle image
        time.sleep(0.3)  # delay before audio messages screen is shown
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()


class MessageResponses_add(Screen, MDApp):
    # 'MessageResponses_add' class allows user to add audio response messages to be played through the doorbell.

    def __init__(self, **kw):
        # assigns the constants which are used in the class and gets the data on existing audio messages
        super().__init__(**kw)
        self.initialUse = jsonStore.get("localData")["initialUse"]  # assigns the value of 'initialUse' to the variable 'self.initialUse' from the local jsonStore
        self.accountID = jsonStore.get("localData")["accountID"]  # assigns the value of 'accounID' to the variable 'self.accountID' from the local jsonStore
        self.dbData_view = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_view["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData'
        response = requests.post(serverBaseURL + "/view_audioMessages",self.dbData_view)  # sends a post request to the 'view_audioMessages' route of the AWS server to fetch all the data about all the audio messages associated with that user
        self.audioMessages = response.json()
        self.numMessages = self.audioMessages["length"]
        self.numPages = int(math.ceil(self.numMessages / 3))
        self.currentPage = 0
        self.currentMessage = -3
        Clock.schedule_once(self.finishInitialising)  # Kivy rules are not applied until the original Widget (MessageResponses_add) has finished instantiating, so must delay the initialisation
        # as the instantiation results in 1 of 2 methods (darkenImage() or create_audioMessages()) being called,
        # each of which requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed

    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation
        # as the instantiation results in 1 of 2 methods (darkenImage() or create_audioMessages()) being called, each of which requires access to Kivy ids to create the GUI
        # and this is only possible if the instantiation is delayed.
        if self.initialUse == "True" and self.numMessages == 0:
            self.ids.pulsingCircle.opacity = 1
        try:
            self.targetView.stop()  # close the target view
        except:
            pass
        self.create_audioMessages(1, 3)

    def create_audioMessages(self, currentPage, currentMessage):
        # method which displays the user's current audio messages and allows users to create new personalised audio messages which can be played through the doorbell
        if self.numMessages == 0: # if the user has not yet recorded any audio messages
            self.ids.plusIcon.pos_hint = {"x": 0.17, "y": 0.5} # sets the position for the plus icon
            self.ids.button_audioMessage_1.disabled = False # activates the button to open the target view widget
            self.target_addMessage() # calls the method which opens the target view widget which explains to the user what a personalised audio message is
        else: # if the user has already added a personalised audio message
            if ((self.currentPage+int(currentPage)) > 0) and (self.currentPage+int(currentPage))<=(self.numPages): # if the new page number that is being transitioned to is positive and less than or equal to the total number of pages required to display all the user's audio messages
                self.currentPage += int(currentPage) # updates the value of the variable 'self.currentPage' depending on whether the user has moved forwards or backwards a page
                if self.currentMessage+int(currentMessage) >= 0:
                    self.currentMessage += int(currentMessage) # updates the value of the variable 'self.currentMessage' depending on whether the user has moved forwards or backwards a page
                if self.currentPage < self.numPages: # if the current page is not the final page required to display all the user's audio messages, then all three icons must be filled with the name of an audio message
                    self.ids.audioMessage_name1.text = self.audioMessages[str(self.currentMessage)][1] # name of the audio message in the top left icon is the first item in the tuple
                    self.ids.audioMessage_name2.text = self.audioMessages[str(self.currentMessage+1)][1] # name of the audio message in the top right icon is the first item in the tuple
                    self.ids.audioMessage_name3.text = self.audioMessages[str(self.currentMessage+2)][1] # name of the audio message in the bottom left icon is the first item in the tuple
                    self.ids.plusIcon.pos_hint = {"x":0.66,"y": 0.24} # position of plus icon image to create a new audio message
                    self.ids.button_audioMessage_1.disabled = False
                    self.ids.button_audioMessage_2.disabled = False
                    self.ids.button_audioMessage_3.disabled = False
                    self.ids.button_plusIcon.disabled = False
                elif self.currentPage == self.numPages: # if the current page is the final page required to display all the user's audio messages
                    self.ids.audioMessage_name1.text = "" # resets the text value for the top left icon
                    self.ids.audioMessage_name2.text = "" # resets the text value for the top right icon
                    self.ids.audioMessage_name3.text = "" # resets the text value for the bottom left icon
                    if self.numMessages % 3 == 1:  # modulus used to determine if there is one audio message on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added one audio message on the page:
                        self.ids.audioMessage_name1.text = self.audioMessages[str(self.currentMessage)][1] # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.65, "y": 0.5} # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                    elif self.numMessages % 3 == 2:  # modulus used to determine if there are two audio messages on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added two audio messages on the page:
                        self.ids.audioMessage_name1.text = self.audioMessages[str(self.currentMessage)][1] # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.audioMessage_name2.text = self.audioMessages[str(self.currentMessage + 1)][1] # name of the audio message in the top right icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.17, "y": 0.24} # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                        self.ids.button_audioMessage_3.disabled = False
                    elif self.numMessages % 3 == 0:  # modulus used to determine if there are three audio messages on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added three audio messages on the page:
                        self.ids.audioMessage_name1.text = self.audioMessages[str(self.currentMessage)][1] # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.audioMessage_name2.text = self.audioMessages[str(self.currentMessage + 1)][1] # name of the audio message in the top right icon is the first item in the tuple
                        self.ids.audioMessage_name3.text = self.audioMessages[str(self.currentMessage + 2)][1] # name of the audio message in the bottom lft icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.66, "y": 0.24} # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                        self.ids.button_audioMessage_3.disabled = False
                        self.ids.button_plusIcon.disabled = False
        self.ids.plusIcon.opacity = 1 # sets the opacity of the plus icon (to add more audio messages) to 1 after placing it/them in the correct position on the screen depending on how many audio messages the user has already added

    def target_addMessage(self):
        # instantiates a target view widget which is displayed on the first use of the app to explain to the user what it means to add an audio message
        self.targetView = MDTapTargetView(
            widget=self.ids.button_audioMessage_1,
            title_text="          Add an audio message",
            description_text="              You can create personalised\n              audio responses which can\n              be easily selected in the\n              SmartBell app and played by\n              "
                             "your SmartBell when a visitor\n              comes to the door.",
            widget_position="left_top",
            outer_circle_color=(49/255, 155/255, 254/255),
            target_circle_color = (145/255, 205/255,241/255),
            outer_radius = 370,
            title_text_size=40,
            description_text_size = 40,
            cancelable= False
        ) # creates the target view widget with the required properties

    def openTarget(self):
        # method which controls the opening of the target view
        self.ids.pulsingCircle.opacity = 0
        if self.targetView.state == "close": # if the target view is currently closed
            self.targetView.start() # opens the target view
            self.ids.button_continueIcon.disabled = False # activates the continue icon button
            animation = Animation(opacity=1,d=0.1)  # automatic animation which gradually increases the opacity of the continue icon image from 0 to 1
            animation.start(self.continueIcon)  # starts the animation of the continue icon image
        else: # if the target view is currently open
            self.targetView.stop() # close the target view
            self.ids.button_continueIcon.disabled = True # deactivates the continue icon button
            animation = Animation(opacity=0, d=0.1)  # automatic animation which gradually decreases the opacity of the continue icon image from 1 to 0
            animation.start(self.continueIcon)  # starts the animation of the continue icon image

    def openMessage(self, buttonNum):
        if buttonNum == 1:
            self.messageDetails = self.audioMessages[str(self.currentMessage)]
        elif buttonNum == 2:
            self.messageDetails = self.audioMessages[str(self.currentMessage+1)]
        elif buttonNum == 3:
            self.messageDetails = self.audioMessages[str(self.currentMessage+2)]
        if self.messageDetails[2] == "Null":
            self.manager.current = "MessageResponses_viewAudio"  # switches to 'MessageResponses_createAudio' GUI
            self.manager.current_screen.__init__() # initialises the running instance of the 'MessageResponses_createAudio' class
            self.manager.current_screen.set_messageDetails(self.messageDetails) # calls the 'set_messageDetails' method of the running instance of the 'MessageResponses_createAudio' class
        else:
            self.manager.current = "MessageResponses_createText"  # switches to 'MessageResponses_createAudio' GUI
            self.manager.current_screen.__init__() # initialises the running instance of the 'MessageResponses_createAudio' class
            self.manager.current_screen.set_messageDetails(self.messageDetails) # calls the 'set_messageDetails' method of the running instance of the 'MessageResponses_createAudio' class

class MessageResponses_create(Screen, MDApp):
    # 'MessageResponses_create' class allows the user to select whether they would like to record their audio message using their voice as the input or type their audio message using the on-screen keyboard as their input. The GUI is created in the kv file.
   pass


class MessageResponses_createAudio(Screen, MDApp):
    # 'MessageResponses_createAudio' class allows users to record their personalised audio message which can be played through their SmartBell doorbell

    def __init__(self, **kw):
        # loads the images/gifs required to create the GUI for the user to record their audio message
        super().__init__(**kw)
        self.initialRecording = True
        self.recordAudio_static = "SmartBell_audioRecord_static.png" # loads the static mic image file
        self.recordAudio_listening = "SmartBell_audioRecord_listening.zip" # loads the zip file used to create the second part of the gif displayed when the user is recording their audio message
        self.recordAudio_loading = "SmartBell_audioRecord_loading.zip" # loads the zip file used to create the third part of the gif displayed when the user is recording their audio message
        self.recordAudio_end = "SmartBell_audioRecord_end.zip" # loads the zip file used to create the final part of the gif displayed when the user is recording their audio message
        Clock.schedule_once(self.finishInitialising)  # Kivy rules are not applied until the original Widget (MessageResponses_createAudio) has finished instantiating, so must delay the initialisation
        # as the instantiation requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed

    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation
        # as the instantiation requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed
        self.ids.recordAudio.source = self.recordAudio_static  # sets the source of the image with id 'recordAudio' to the static microphone image
        self.ids.button_recordAudio.disabled = False  # activates the button to record an audio message


    def rerecordAudio(self, messageDetails):
        self.messageDetails = messageDetails

    def startRecording(self):
        # method which begins the process of recording the user's audio message

        self.recordAudio = recordAudio() # instantiates the method which is used to control the recording of the user's audio message
        self.recordAudio_thread = threading.Thread(target=self.recordAudio.start, args=(),daemon=False)  # initialises the instance of thread which is used to record the user's audio input
        self.ids.recordAudio.anim_loop = 0 # sets the number of loops of the gif to be played (which uses the zio file 'SmartBell_audioRecord_listening.zip') to infinite as the length of the user's audio message is indeterminate
        self.ids.recordAudio.source = self.recordAudio_listening # changes the source of the image with the id 'recordAudio'
        self.startTime = time.time()  # sets up timer to record how long button to record audio is held for
        self.recordAudio_thread.start()  # starts the thread instance called 'self.recordAudio_thread'

    def stopRecording(self):
        # method which terminates the recording of the user's audio message
        self.ids.recordAudio.source = self.recordAudio_static # changes the source of the image with the id 'recordAudio'
        self.endTime = time.time() # stops the timer which records how long button to record audio is held for
        if (self.endTime - self.startTime) <= 1:  # if this audio recording is too short, an error message will be returned
            self.recordAudio.falseStop() # calls the method which clears the data stored from the recording as the recording was too short and therefore is invalid
            self.ids.snackbar.font_size = 36
            self.ids.snackbar.text = "Press and hold the microphone to speak"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.openSnackbar() # calls the method which opens the snackbar to indicate that the audio message recorded was too short
            self.dismissSnackbar_thread = threading.Thread(target=self.dismissSnackbar, args=(),
                                                            daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
            self.dismissSnackbar_thread.start() # starts the thread 'self.dismissSnackbar_thread'
        else: # if the button to record audio is held for more than one second
            self.ids.button_recordAudio.disabled = True # disables the button to record an audio message
            self.audioData = self.recordAudio.stop() # calls the method which terminates the recording of the user's voice input and saves the audio data
            with open(join((App.get_running_app().user_data_dir.replace("createAudio", "viewAudio")),"audioMessage_tmp.pkl"), "wb") as file: # create pkl file with name equal to the messageID in write bytes mode
                pickle.dump(self.audioData, file) # 'pickle' module serializes the data stored in the object (list) 'self.audioData' into a byte stream which is stored in pkl file
                file.close() # closes the file
            self.manager.current = "MessageResponses_viewAudio"  # switches to 'MessageResponses_viewAudio' GUI
            self.manager.current_screen.__init__()  # initialises the running instance of the 'MessageResponses_createAudio' class
            if self.initialRecording == False:
                self.manager.current_screen.set_messageDetails(self.messageDetails)  # calls the 'set_messageDetails' method of the running instance of the 'MessageResponses_createAudio' class

    def helpAudio(self):
        # method which instructs the user how to record an audio message if they press the 'Help' button
        self.ids.snackbar.font_size = 36
        self.ids.snackbar.text = "Press and hold the microphone to speak"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
        self.openSnackbar()  # calls the method which opens the snackbar to indicate that the audio message recorded was too short
        self.dismissSnackbar_thread = threading.Thread(target=self.dismissSnackbar, args=(),
                                                       daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
        self.dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'

    def openSnackbar(self):
        # method which controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0.13},
                              d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # method which controls the closing animation of the snackbar
        time.sleep(3.5)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0},
                              d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation


class recordAudio(Screen):
    # 'recordAudio' class allows user to create personalised audio messages using voice input
    def __init__(self, **kw):
        # initialises constant properties for the class
        super().__init__(**kw)
        self.samples_per_second = 60 # variables which stores the number of audio samples recorded per second
        self.audioData = [] # creates a list to store the audio bytes recorded
        self.mic = get_input(callback=self.micCallback, rate=8000, source='default', buffersize=2048) # initialises the method 'get_input' from the module 'audiostream' with the properties required to ensure the audio is recorded correctly
        print("init")

    def micCallback(self, buffer):
        # method which is called by the method 'get_input' to store recorded audio data (each buffer of audio samples)
        self.audioData.append(buffer) # appends each buffer (chunk of audio data) to variable 'self.audioData'
        print("buffer")

    def start(self):
        # method which begins the process of recording the audio data
        self.mic.start() # starts the method 'self.mic' recording audio data
        Clock.schedule_interval(self.readChunk, 1 / self.samples_per_second) # calls the method 'self.readChunk' to read and store each audio buffer (2048 samples) 60 times per second
        print("start")

    def readChunk(self, sampleRate):
        # method which coordinates the reading and storing of the bytes from each buffer of audio data (which is a chunk of 2048 samples)
        self.mic.poll()  # calls 'get_input(callback=self.mic_callback, source='mic', buffersize=2048)' to read the byte content. This byte content is then dispatched to the callback method 'self.micCallback'
        print("chunk")

    def falseStop(self):
        # method which terminates the audio recording when the duration of audio recording is less than 1 second
        self.audioData = [] # clears the list storing the audio data
        Clock.unschedule(self.readChunk) # un-schedules the Clock's rythmic execution of the 'self.readChunk' callback
        self.mic.stop() # stops recording audio

    def stop(self):
        # method which terminates and saves the audio recording when the recording has been successful
        Clock.unschedule(self.readChunk) # un-schedules the Clock's rythmic execution of the 'self.readChunk' callback
        self.mic.stop() # stops recording audio
        return self.audioData


class MessageResponses_review(Screen, MDApp):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.accountID = jsonStore.get("localData")["accountID"]  # assigns the value of 'accounID' to the variable 'self.accountID' from the local jsonStore

    def set_messageDetails(self, messageDetails):
        self.messageDetails = messageDetails
        self.messageID = self.messageDetails[0]
        self.messageName = self.messageDetails[1]
        self.messageText = self.messageDetails[2]
        self.initialRecording = False
        self.initialTyping = False
        try:
            self.ids.previousMessage.text = self.messageText
            self.ids.previousMessage_heading.text = "The current text of your audio message:"
            self.ids.previousMessage.opacity = 1
        except:
            pass

    def nameMessage_dialog(self):
        # method which allows the user to input the name of the audio message which they recorded/typed
        print(self.initialRecording)
        print(self.messageType)
        if (self.initialRecording == False and self.messageType == "Voice") or (self.initialTyping == False and self.messageType == "Text"):
            title = "Enter a new name for this audio message or press 'cancel' to keep it named '{}':".format(self.messageName)
        else:
            title = "What would you like to name your audio message?"
        self.dialog = MDDialog(
            title=title,
            auto_dismiss=False,
            type="custom",
            content_cls=nameMessage_content(),  # content class
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1), on_press = self.dismissDialog),
                     MDRaisedButton(text="SAVE", md_bg_color = (136/255,122/255,239/255,1), on_press=self.nameMessage)]) # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open() # opens the dialog box

    def dismissDialog(self, instance):
        # method which is called when 'Cancel' is tapped on the dialog box
        self.dialog.dismiss()  # closes the dialog box
        if (self.initialRecording == False and self.messageType == "Voice") or (self.initialTyping == False and self.messageType == "Text"):
            self.update_audioMessages()

    def nameMessage(self, instance):
        # method which is called when the button 'Save' is tapped on the dialog box which allows the user to input the name of the audio message they recorded/typed
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the audio message they recorded/typed
            if isinstance(object, MDTextField): # if the object is an MDTextField
                self.dbData_name = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
                self.dbData_name["messageName"] = object.text  # adds the variable 'object.text' to the dictionary 'dbData_create'
                self.dbData_name["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_create'
                response = requests.post(serverBaseURL + "/verify_messageName", self.dbData_name)  # sends post request to 'verify_messageName' route on AWS server to check whether the message name that the user has inputted has already been assigned to one of their audio messages
                if (((self.initialRecording == False and self.messageType == "Voice") or (self.initialTyping == False and self.messageType == "Text")) and (object.text == "" or (response.text == "exists" and response.text != self.messageName) or len(object.text) > 13)) or (((self.initialRecording == False and self.messageType == "Voice") or (self.initialTyping == False and self.messageType == "Text")) and (object.text == "" or response.text == "exists" or len(object.text) > 13)): # if the user has not inputted any text or if the message name is already in use by that user or if the length of the message name is greater than 13 characters
                    xCood = int(instance.pos[0]) # assigns current x coordinate of the 'Save' button to the variable 'xCood'
                    yCood = int(instance.pos[1]) # assigns current y coordinate of the 'Save' button to the variable 'yCood'
                    animation = Animation(pos=((xCood + 7), yCood), t="out_elastic", d=0.02)  # creates an animation object which moves the 'Save' button to the right
                    animation += Animation(pos=((xCood - 7), yCood), t="out_elastic", d=0.02) # adds a sequential step to the animation object which moves the 'Save' button to the left
                    animation += Animation(pos=(xCood, yCood), t="out_elastic", d=0.02) # adds a sequential step to the animation object which moves the 'Save' button to its original position
                    animation.start(instance) # starts the animation instance
                else: # if the user has inputted a name which is not already in use by that user and is 13 or less characters in length
                    if (self.initialRecording == True and self.messageType == "Voice") or (self.initialTyping == True and self.messageType == "Text"): # if this audio message has just been recorded
                        self.messageID = self.create_messageID()  # calls the method which creates a unique messageID for the audio message which the user has created
                        if self.initialRecording == True and self.messageType == "Voice":
                            oldName = join(App.get_running_app().user_data_dir,"audioMessage_tmp.pkl")
                            newName = join(App.get_running_app().user_data_dir,(self.messageID + ".pkl"))
                            os.rename(oldName, newName)
                            oldName = join(App.get_running_app().user_data_dir,"audioMessage_tmp.wav")
                            newName = join(App.get_running_app().user_data_dir,(self.messageID + ".wav"))
                            os.rename(oldName, newName)
                    self.dialog.dismiss()  # closes the dialog box
                    self.messageName = object.text # assigns the text of the MDTextField to the variable 'self.messageName' (the text is the name of the audio message as inputted by the user)
                    self.update_audioMessages()  # calls the method to update the MySQL table 'audioMessages'

    def create_messageID(self):
        # creates a unique messageID for the audio message created by the user
        self.dbData_create = dbData # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        while True: # creates an infinite loop
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
            messageID = ''.join(random.choice(chars) for i in range(
                16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique messageID
            self.dbData_create["messageID"] = messageID # adds the variable 'messageID' to the dictionary 'dbData_create'
            response = requests.post(serverBaseURL + "/verify_messageID", self.dbData_create) # sends post request to 'verify_messageID' route on AWS server to check whether the messageID that has been generated for an audio message does not already exist
            if response.text == "notExists": # if the messageID does not yet exist
                break # breaks the infinite loop
            else:
                pass
        return messageID # returns the unique message ID generated for this audio message

    def deleteMessage(self):
        self.dbData_update = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/delete_audioMessages", self.dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'


class MessageResponses_viewAudio(MessageResponses_review, Screen, MDApp):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.playbackAudio_gif = "SmartBell_playbackAudio.zip"  # loads the zip file used to create the audio playback gif
        self.playbackAudio_static = "SmartBell_playbackAudio.png"  # loads the image file of the audio playback static image
        self.initialRecording = True
        self.initialTyping = None
        self.messageType = "Voice"
        self.messageID = "audioMessage_tmp"

    def update_audioMessages(self):
        # method which updates the MySQL table to store the data about the audio message created by the user
        self.dbData_update = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        self.dbData_update["messageName"] = self.messageName  # adds the variable 'messageName' to the dictionary 'dbData_update'
        self.dbData_update["fileText"] = "Null"  # adds the 'null' variable 'fileText' to the dictionary 'dbData_update'
        self.dbData_update["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_update'
        self.dbData_update["initialCreation"] = str(self.initialRecording)  # adds the variable 'initialRecording' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/update_audioMessages", self.dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'
        self.uploadAWS()  # calls the method to upload the audio message data to AWS S3

    def uploadAWS(self):
        # method which sends the data for the audio message recorded by the user as a pkl file to the AWS elastic beanstalk environment, where it is uploaded to AWS s3 using 'boto3' module
        self.uploadData = {"bucketName": "nea-audio-messages",
                           "s3File": self.messageID + ".pkl"}  # creates the dictionary which stores the metadata required to upload the personalised audio message to AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
        file = {"file": open(join(App.get_running_app().user_data_dir, self.messageID+".pkl"), "rb")} # opens the file to be sent using Flask's 'request' method (which contains the byte stream of audio data) and stores the file in a dictionary
        #file = {"file": open(self.messageID + ".pkl", "rb")}
        response = requests.post(serverBaseURL + "/uploadS3", files=file,
                                 data=self.uploadData)  # sends post request to 'uploadS3' route on AWS server to upload the pkl file storing the data about the audio message to AWS s3 using 'boto3'
        # This is done because the 'boto3' module cannot be installed on mobile phones so the process of uploading the pkl file to AWS s3 using boto3 must be done remotely on the AWS elastic beanstalk environment
        self.loggedIn = jsonStore.get("localData")["loggedIn"]
        jsonStore.put("localData", initialUse="False", loggedIn=self.loggedIn, accountID=self.accountID)
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class

    def play_audioMessage(self):
        # method which allows user to playback the audio message which they have recorded
        #self.fileName = copy.deepcopy(self.messageID)
        self.fileName = join(App.get_running_app().user_data_dir, self.messageID)
        if self.messageID != "audioMessage_tmp":
            try:
                self.messageFile_voice = SoundLoader.load(self.fileName + ".wav")
                if self.messageFile_voice.length != 0:
                    pass
                    print("wav on computer")
            except:
                pass
        else:
            try:
                with open(self.fileName+".pkl", "rb") as file:
                    self.audioData = pickle.load(file)
                    file.close()  # closes the file
                    print("pkl on computer")
            except:
                self.downloadData = {"bucketName": "nea-audio-messages",
                                     "s3File": self.fileName + ".pkl"}  # creates the dictionary which stores the metadata required to download the pkl file of the personalised audio message from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
                response = requests.post(serverBaseURL + "/downloadPkl", self.downloadData)
                self.audioData = response.content
                with open(join(self.fileName + ".pkl"), "wb") as file:
                    pickle.dump(response.content,file)  # 'pickle' module serializes the data stored in the object (list) 'self.audioData' into a byte stream which is stored in pkl file
                    file.close()  # closes the file
                    print("pkl on AWS")
            self.messageFile = wave.open((self.fileName + ".wav"), "wb")
            self.messageFile.setnchannels(1)  # change to 1 for audio stream module
            self.messageFile.setsampwidth(2)
            self.messageFile.setframerate(8000)  # change to 8000 for audio stream module
            self.messageFile.writeframes(b''.join(self.audioData))
            self.messageFile.close()
        self.messageFile_voice = SoundLoader.load(self.fileName + ".wav")
        self.messageFile_voice.play()
        self.ids.playbackAudio.source = self.playbackAudio_gif
        self.audioLength = self.messageFile_voice.length
        self.thread_stopGif = threading.Thread(target=self.stopGif, args=(),
                                               daemon=False)  # initialises an instance of the 'threading.Thread()' method
        self.thread_stopGif.start()  # starts the thread which will run in pseudo-parallel to the rest of the program

    def stopGif(self):
        time.sleep(self.audioLength)
        self.ids.playbackAudio.source = self.playbackAudio_static


class MessageResponses_createText(MessageResponses_review, Screen, MDApp):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.initialTyping = True
        self.initialRecording = None
        self.messageType = "Text"

    def save_textMessage(self):
        if self.initialTyping == False and len(list((self.ids.textMessage.text).strip())) == 0:
            self.nameMessage_dialog()
        elif (len(list((self.ids.textMessage.text).strip())) > 80 or len(list((self.ids.textMessage.text).strip())) == 0):
            self.ids.snackbar.font_size = 30
            self.ids.snackbar.text = "Sorry, the text you have entered is invalid!\nPlease make sure your message is between\n1 and 80 characters."  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.openSnackbar()  # calls the method which opens the snackbar to indicate that the audio message recorded was too short
            self.dismissSnackbar_thread = threading.Thread(target=self.dismissSnackbar, args=(),
                                                           daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
            self.dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'
        else:
            self.nameMessage_dialog()

    def update_audioMessages(self):
        # method which updates the MySQL table to store the data about the audio message created by the user
        self.textMessage = self.ids.textMessage.text
        self.dbData_update = dbData  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        self.dbData_update["messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        self.dbData_update["messageName"] = self.messageName  # adds the variable 'messageName' to the dictionary 'dbData_update'
        self.dbData_update["fileText"] = self.textMessage # adds the 'null' variable 'fileText' to the dictionary 'dbData_update'
        self.dbData_update["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_update'
        self.dbData_update["initialCreation"] = str(self.initialTyping)  # adds the variable 'initialRecording' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/update_audioMessages",self.dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'
        self.loggedIn = jsonStore.get("localData")["loggedIn"]
        jsonStore.put("localData", initialUse="False", loggedIn=self.loggedIn, accountID=self.accountID)
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class

    def openSnackbar(self):
        # method which controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0.13},
                              d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # method which controls the closing animation of the snackbar
        time.sleep(3.5)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0},
                              d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation

class nameMessage_content(BoxLayout):
    # 'nameMessage_content' class creates the specific graphic elements for the dialog box which allows the user to enter the name of the audio message. The GUI is created in the kv file.
    pass


class MyApp(MDApp):
    # 'MyApp' class is used to create app GUI by building 'layout.kv' file
    def build(self, **kw):
        layout = Builder.load_file("layout.kv")  # loads the 'layout.kv' file
        return layout


if __name__ == "__main__":  # when the program is launched, if the name of the file is the main program (i.e. it is not a module being imported by another file) then this selection statement is True
    MyApp().run()  # the run method is inherited from the 'MDApp' class which is inherited by the class 'MyApp'

