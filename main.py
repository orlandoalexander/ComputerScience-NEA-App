import os
os.environ[
    'KIVY_AUDIO'] = 'avplayer' # control the kivy environment to ensure audio input can be accepted following audio output
from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.taptargetview import MDTapTargetView
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.list import TwoLineAvatarListItem
from kivymd.uix.list import ImageLeftWidget
from kivy.uix.image import AsyncImage
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from os.path import join
import re
import random
import string
import requests
import hashlib
from threading import Thread
import time
import math
import wave
from pyobjus import autoclass
from audiostream import get_input
import pickle


serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"  # base URL to access AWS elastic beanstalk environment


class WindowManager(ScreenManager):
    # 'WindowManager' class used for transitions between GUI windows
    pass


class Launch(Screen, MDApp):
    # coordinate the correct launch screen for the mobile app depending on the current status of the app

    def __init__(self, **kw):
        super().__init__(**kw)
        self.statusUpdate()
        Clock.schedule_once(self.finishInitialising)  # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay initialisation

    def finishInitialising(self, dt):
        # applies launch processes which require access to Kivy ids
        self.manager.transition = NoTransition() # set transition type
        if self.initialUse == True: # initial launch of mobile app
            self.manager.current = "SignUp"
        elif self.loggedIn == True: # user already logged in
            createThread_ring(self.accountID, self.filepath) # connect to MQTT broker to receive messages when visitor presses doorbell
            self.manager.current = "Homepage"  # if the user is already logged in, screen 'Homepage' is called to allow the user to navigate the app
        else: # not initial launch of app and user not logged in
            self.manager.current = "SignIn"

    def statusUpdate(self):
        # update the attributes assigned to the locally cached data about the user details and the app status
        self.filepath = MDApp.get_running_app().user_data_dir # path to readable/writeable directory to store local data
        jsonFilename = join(self.filepath,"jsonStore.json")  # if file name already exists, it is assigned to 'self.filename'. If filename doesn't already exist, file is created locally on the mobile phone
        self.jsonStore = JsonStore(jsonFilename)  # wraps the json file as a json object
        if not self.jsonStore.exists("localData"): # if the mobile app is running for the first time, the key 'localData' will not exist
            self.jsonStore.put("localData", initialUse=True, loggedIn=False, accountID="", paired=False) # sets launch properties
        self.initialUse = self.jsonStore.get("localData")["initialUse"]
        self.loggedIn = self.jsonStore.get("localData")["loggedIn"]
        self.paired = self.jsonStore.get("localData")["paired"]
        self.accountID = self.jsonStore.get("localData")["accountID"]

    def dismissDialog(self, instance):
        # called when 'Cancel' is tapped on the dialog box
        self.dialog.dismiss()  # closes the dialog box

    def openSnackbar(self):
        # controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": self.topHeight}, d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # controls the closing animation of the snackbar
        time.sleep(self.sleepTime)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0}, d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation


class Homepage(Launch):
    # home screen allows user to navigate to each screen in mobile app

    def pairSelect(self, **kw):
        # called when user selects 'Pair' button on home screen
        super().__init__(**kw)
        self.statusUpdate()
        if self.paired == False: # user account not paired with doorbell
            title = f"Enter the name of the SmartBell which you would like to pair with:"
            self.pairDialog(title) # open dialog to allow user to pair with doorbell
        else:
            self.piID=self.paired
            self.alreadyPaired_dialog()

    def account(self):
        # called when user taps 'Account' icon on home screen
        self.statusUpdate()
        self.signOut_dialog() # open dialog which gives user the option to sign out of their account

    def signOut(self, instance):
        # signs user out of their account
        self.dialog.dismiss()
        self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=False, accountID='', paired=False)
        print(self.jsonStore.get("localData"))
        self.statusUpdate()
        MDApp.get_running_app().manager.get_screen('SignUp').ids.firstName.text = ''
        MDApp.get_running_app().manager.get_screen('SignUp').ids.surname.text = ''
        MDApp.get_running_app().manager.get_screen('SignUp').ids.email.text = ''
        MDApp.get_running_app().manager.get_screen('SignUp').ids.password.text = ''
        MDApp.get_running_app().manager.get_screen('SignIn').ids.email.text = ''
        MDApp.get_running_app().manager.get_screen('SignIn').ids.password.text = ''
        self.manager.current = "SignIn"

    def signOut_dialog(self):
        # creates dialog box to ask user to confirm whether they would like to sign out of their account
        self.dialog = MDDialog(
            title='Sign out?',
            text = 'If you sign out, you will be unpaired from any existing connection with a SmartBell.',
            auto_dismiss=False,
            type="custom",
            buttons=[MDFlatButton(text="NO", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text='YES', md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.signOut)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box

    def pairDialog(self, title):
        # creates dialog to enable user to enter ID of SmartBell to pair with
        self.dialog = MDDialog(
            title=title,
            auto_dismiss=False,
            type="custom",
            content_cls=DialogContent(),  # content class
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text='ENTER', md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.pair)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box

    def alreadyPaired_dialog(self):
        # creates dialog asking user to confirm whether they would like to alter their current SmartBell pairing
        self.dialog = MDDialog(
            title=f"You are currently paired with SmartBell '{self.piID}'.\nDo you want to unpair / pair with a new SmartBell?",
            auto_dismiss=False,
            type="custom",
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text='UNPAIR / PAIR', md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.dismissDialog_alreadyPaired)])
        self.dialog.open()  # opens the dialog box

    def dismissDialog_alreadyPaired(self, instance):
        # creates dialog to enable to unpair from current SmartBell or pair with new SmartBell
        self.dialog.dismiss()  # closes the dialog box
        title = f"Enter the name of the SmartBell which you would like to pair with. Alternatively, enter 'unpair' to unpair from SmartBell '{self.piID}':"
        self.pairDialog(title)

    def pair(self, instance):
        # executes SmartBell pairing process
        self.dialog.dismiss()
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the audio message they recorded/typed
            if isinstance(object, MDTextField):  # if the object is an MDTextField
                newID = object.text
        if newID.lower() == 'unpair':
            self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=self.loggedIn, accountID=self.accountID,
                          paired=False) # write updated data to the json file
            self.statusUpdate()  # update launch variables
            publishData = ""
            id = self.piID
            pairing = False
            pair_thread = Thread(target=pairThread, args=(self.accountID, id, pairing, self.jsonStore))
            pair_thread.start()
        else:
            self.piID= newID
            publishData = str(self.accountID)
            dbData_id = {'id': self.piID}
            response = (requests.post(serverBaseURL + "/checkPairing", dbData_id)).text
            if response == 'notExists': # if SmartBell with ID entered by user doesn't exist
                self.ids.snackbar.text = f"No SmartBell with the name '{self.piID}' exists!"
                self.topHeight = 0.13
                self.sleepTime = 5
                self.openSnackbar() # calls the method which creates the snackbar animation
                thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
                thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
            elif response == 'exists':
                pairing = True
                pair_thread = Thread(target=pairThread, args=(self.accountID, self.piID, pairing, self.jsonStore))
                pair_thread.start()
        MQTTPython = autoclass('MQTT') # interface between Python code and objective C class 'MQTT'
        mqtt = MQTTPython.alloc().init()
        mqtt.publishData = publishData
        mqtt.publishTopic = f"id/{self.piID}"
        mqtt.publish() # publish message to MQTT topic 'id/piID' via objective C class 'MQTT'


class SignUp(Launch):
    # 'SignUp' class allows user to create an account

    def createAccount(self):
        # called when user taps the Sign Up button to check validity of details entered by user
        self.firstName_valid = False  # variable which indicates that a valid value for 'firstName' has been inputted by the user
        self.surnameValid = False  # variable which indicates that a valid value for 'surname' has been inputted by the user
        self.emailValid = False  # variable which indicates that a valid value for 'email' has been inputted by the user
        self.passwordValid = False  # variable which indicates that a valid value for 'password' has been inputted by the user
        if self.ids.firstName.text == "":  # if no data is inputted...
            self.ids.firstName_error.opacity = 1  # ...then an error message is displayed
        else:
            self.firstName = self.ids.firstName.text  # inputted first name assigned to a variable
            self.ids.firstName_error.opacity = 0  # error message removed
            self.firstName_valid = True  # variable which indicates that a valid value has been inputted by the user
        if self.ids.surname.text == "":  # if no data is inputted...
            self.ids.surname_error.opacity = 1  # ...then an error message is displayed
        else:
            self.surname = self.ids.surname.text  # inputted surname assigned to a variable
            self.ids.surname_error.opacity = 0  # error message removed
            self.surnameValid = True  # variable which indicates that a valid value has been inputted by the user
        if self.ids.email.text == "":  # if no data is inputted...
            self.ids.email_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.email_error_invalid.opacity = 0  # invalid email error message is removed
        else:
            email = self.ids.email.text
            if re.search(".+@.+\..+", email) != None:  # regular expression used to check that inputted email is in a valid email format
                self.email = self.ids.email.text  # inputted email assigned to a variable
                self.ids.email_error_blank.opacity = 0  # error message removed
                self.ids.email_error_invalid.opacity = 0  # invalid email error message removed
                self.emailValid = True  # variable which indicates that a valid value has been inputted by the user
            else:
                self.ids.email_error_blank.opacity = 0  # blank data error message removed
                self.ids.email_error_invalid.opacity = 1  # invalid email error message displayed
        if self.ids.password.text == "":  # if no data is inputted...
            self.ids.password_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
        else:
            password = self.ids.password.text
            if re.search("(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[a-zA-Z\d@$!%*?&]{8,}", password) != None:
                # Checks that inputted password is at least 8 characters
                # Regular expression used to check that password contains at least 1 lowercase character,
                # 1 uppercase character, 1 digit and 1 special character
                self.password = self.ids.password.text  # inputted password assigned to a variable
                self.hashedPassword = (hashlib.new("sha3_256", self.password.encode())).hexdigest()
                # Creates a hash of the user's password so that it is stored secureley on the database, as it is sensitive data

                self.ids.password_error_blank.opacity = 0  # error message removed
                self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
                self.passwordValid = True  # variable which indicates that a valid value has been inputted by the user
                if self.firstName_valid and self.surnameValid and self.emailValid and self.passwordValid:  # checks if all the data values have been inputted and are valid
                    self.createAccountID()  # method called to create a unique accountID for the user
            else:
                self.ids.password_error_blank.opacity = 0  # blank data error message removed
                self.ids.password_error_invalid.opacity = 1  # invalid password error message displayed

    def createAccountID(self):
        # creates a unique accountID for the user
        data_accountID = {"field": "accountID"}
        self.accountID = requests.post(serverBaseURL + "/create_ID", data_accountID).text
        self.updateUsers()

    def updateUsers(self):
        # add user's details to 'users' table in AWS RDS database
        dbData_update = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_update["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData'
        dbData_update["firstName"] = self.firstName  # adds the variable 'firstName' to the dictionary 'dbData'
        dbData_update["surname"] = self.surname  # adds the variable 'surname' to the dictionary 'dbData'
        dbData_update["email"] = self.email  # adds the variable 'email' to the dictionary 'dbData'
        dbData_update[
            "password"] = self.hashedPassword  # adds the variable 'hashPassword' to the dictionary 'dbData'
        response = requests.post(serverBaseURL + "/verifyAccount",
                                 dbData_update)  # sends post request to 'verifyAccount' route on AWS server to check whether the email address inputted is already associated with an account
        self.topHeight = 0.13 # snackbar properties
        self.sleepTime = 5
        if response.text == "exists":  # if the inputted email address is already associated with an account
            self.ids.snackbar.text = "Account with this email address already exists. Login instead"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.ids.snackbar.font_size = 24
            self.openSnackbar() # calls the method which creates the snackbar animation
            thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                 daemon=False)  # initialises an instance of the 'threading.Thread()' method
            thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
        else:
            response = requests.post(serverBaseURL + "/updateUsers",
                                     dbData_update)  # sends post request to 'updateUsers' route on AWS server with user's inputted data to be stored in the database
            if response.text == "error":  # if an error occurs when adding the user's data into the 'users' table
                self.ids.snackbar.text = "Error creating account. Please try again later"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
                self.ids.snackbar.font_size = 30
                self.openSnackbar() # calls the method which creates the snackbar animation
                thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
                thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
            else:
                self.statusUpdate() # get latest value of 'paired'
                self.jsonStore.put("localData", initialUse=self.initialUse,
                              loggedIn=True, accountID=self.accountID,
                              paired=self.paired)  # updates json object to reflect that user has successfully created an account
                self.statusUpdate()  # update launch variables


                createThread_ring(self.accountID, self.filepath) # connect to MQTT broker to receive messages when visitor presses doorbell as now logged in and have unique accountID

                self.manager.transition = NoTransition()  # creates a cut transition type

                if self.initialUse == True:
                    self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
                    self.manager.current.__init__()
                else:
                    self.manager.current = "Homepage"  # switches to 'Homepage' GUI
                    self.manager.current.__init__()



class SignIn(Launch):
    # 'SignIn' class allows users to log into their account

    def signIn(self):
        # called when user taps the Sign In button
        self.emailValid = False  # variable which indicates that a valid value has been inputted by the user
        self.passwordValid = False  # variable which indicates that a valid value has been inputted by the user
        if self.ids.email.text == "":  # if no data is inputted...
            self.ids.email_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.email_error_invalid.opacity = 0  # invalid email error message is removed
        else:
            self.email = self.ids.email.text  # inputted email assigned to a variable
            self.ids.email_error_blank.opacity = 0  # error message removed
            self.emailValid = True
        if self.ids.password.text == "":  # if no data is inputted...
            self.ids.password_error_blank.opacity = 1  # ...then an error message is displayed
            self.ids.password_error_invalid.opacity = 0  # invalid password error message is removed
        else:
            self.password = self.ids.password.text  # inputted password assigned to a variable
            self.hashedPassword = (hashlib.new("sha3_256",self.password.encode())).hexdigest()
            # Creates a hash of the user's password so that it can be compared to the hashed version stored on the database
            self.ids.password_error_invalid.opacity = 0  # error message removed
            self.passwordValid = True  # variable which indicates that a valid value has been inputted by the user
            if self.emailValid and self.passwordValid:  # checks if all the data values have been inputted and are valid
                self.verifyUser()

    def verifyUser(self):
        # verifies the email and password entered by the user
        dbData_verify = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_verify["email"] = self.email  # adds the variable 'email' to the dictionary 'dbData'
        dbData_verify["password"] = self.hashedPassword  # adds the variable 'password' to the dictionary 'dbData'
        response = (requests.post(serverBaseURL + "/verifyUser", dbData_verify)).json()[
            'result']  # sends a post request to the 'verifyUser' route of the AWS server to validate the details (email and password) entered by the user
        if response == "none":  # if the details inputted by the user don't match an existing account
            self.topHeight =0.1
            self.sleepTime = 3.5
            self.openSnackbar() # calls the method which creates the snackbar animation
            thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                 daemon=False)  # initialises an instance of the 'threading.Thread()' method
            thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
        else:
            self.accountID = response  # if the user inputs details which match an account stored in the MySQL database, their unique accountID is returned
            dbData_accountID = {'accountID': self.accountID}
            response = (requests.post(serverBaseURL + "/getPairing", dbData_accountID).json())[
                'result']  # sends post request to 'verifyAccount' route on AWS server to check whether the email address inputted is already associated with an account
            if response == 'none':  # if there is no doorbell pairing for this account
                self.paired = self.jsonStore.get("localData")["paired"]
                self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=True, accountID=self.accountID,
                              paired=self.paired)  # updates json object to reflect that user has successfully signed in
            else:
                doorbellID = response
                self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=True, accountID=self.accountID,
                              paired=doorbellID)  # updates json object to reflect that user has successfully signed in
            self.statusUpdate()  # update launch variables

            createThread_ring(self.accountID, self.filepath) # connect to MQTT broker to receive messages when visitor presses doorbell as now logged in

            self.manager.transition = NoTransition()  # creates a cut transition type

            self.manager.current = "Homepage"  # switches to 'Homepage' GUI
            self.manager.current.__init__()


class MessageResponses_add(Launch):
    # 'MessageResponses_add' class allows user to add audio response messages to be played through the doorbell.

    def __init__(self, **kw):
        # retrieves the data for existing audio messages
        super().__init__(**kw)
        dbData_view = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_view["accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData'
        response = (requests.post(serverBaseURL + "/view_audioMessages", dbData_view)).json()[
            'result']  # sends a post request to the 'view_audioMessages' route of the AWS server to fetch all the data about all the audio messages associated with that user
        if response == 'none':
            self.numMessages = 0
            self.messageData = []
        else:
            self.messageData = response
            self.numMessages = self.messageData["length"]
        self.numPages = int(math.ceil(self.numMessages / 3))
        self.currentPage = 0
        self.currentMessage = -3
        self.previewMessages = False
        try:
            self.targetView.stop()  # close the target view
        except:
            pass
        Clock.schedule_once(
            self.finishInitialising)  # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay initialisation

    def finishInitialising(self, dt):
        # applies initialisation processes which require access to Kivy ids
        if self.initialUse == True and self.numMessages == 0: # if the mobile app is running for the first time and the user has zero audio messages
            # create animation:
            animation = Animation(color=[1, 1, 1, 0], duration=0.1)  # become invisible
            animation += Animation(color=[1, 1, 1, 0], duration=1)  # invisible
            animation += Animation(color=[1, 1, 1, 1], duration=0.1)  # become visible
            animation += Animation(color=[1, 1, 1, 1], duration=1)  # visible
            animation.repeat = True  # animation loops forever
            animation.start(self.ids.plusIcon) # apply animation to image with id 'plusIcon'
        self.audioMessage_create(1, 3) # calls method to display user's current audio messages


    def audioMessage_create(self, currentPage, currentMessage):
        # displays the user's current audio messages and allows users to create new personalised audio messages which can be played through the doorbell
        if self.numMessages == 0:  # if the user has not yet recorded any audio messages
            self.addMessage_target()  # calls the method which opens the target view widget which explains to the user what a personalised audio message is
            self.ids.plusIcon.pos_hint = {"x": 0.17, "y": 0.5}  # sets the position for the plus icon
            self.ids.button_audioMessage_1.disabled = False  # activates the button to open the target view widget
        else:  # if the user has already added a personalised audio message
            self.jsonStore.put("localData", initialUse=False, loggedIn=self.loggedIn, accountID=self.accountID,
                               paired=self.paired)
            self.statusUpdate()
            if ((self.currentPage + int(currentPage)) > 0) and (self.currentPage + int(currentPage)) <= (
            self.numPages):  # if the new page number that is being transitioned to is positive and less than or equal to the total number of pages required to display all the user's audio messages
                self.currentPage += int(
                    currentPage)  # updates the value of the variable 'self.currentPage' depending on whether the user has moved forwards or backwards a page
                if self.currentMessage + int(currentMessage) >= 0:
                    self.currentMessage += int(
                        currentMessage)  # updates the value of the variable 'self.currentMessage' depending on whether the user has moved forwards or backwards a page
                if self.currentPage < self.numPages:  # if the current page is not the final page required to display all the user's audio messages, then all three icons must be filled with the name of an audio message
                    self.ids.audioMessage_name1.text = self.messageData[str(self.currentMessage)][
                        1]  # name of the audio message in the top left icon is the first item in the tuple
                    self.ids.audioMessage_name2.text = self.messageData[str(self.currentMessage + 1)][
                        1]  # name of the audio message in the top right icon is the first item in the tuple
                    self.ids.audioMessage_name3.text = self.messageData[str(self.currentMessage + 2)][
                        1]  # name of the audio message in the bottom left icon is the first item in the tuple
                    self.ids.plusIcon.pos_hint = {"x": 0.66,
                                                  "y": 0.24}  # position of plus icon image to create a new audio message
                    self.ids.button_audioMessage_1.disabled = False
                    self.ids.button_audioMessage_2.disabled = False
                    self.ids.button_audioMessage_3.disabled = False
                    self.ids.button_plusIcon.disabled = False
                elif self.currentPage == self.numPages:  # if the current page is the final page required to display all the user's audio messages
                    self.ids.audioMessage_name1.text = ""  # resets the text value for the top left icon
                    self.ids.audioMessage_name2.text = ""  # resets the text value for the top right icon
                    self.ids.audioMessage_name3.text = ""  # resets the text value for the bottom left icon
                    if self.numMessages % 3 == 1:  # modulus used to determine if there is one audio message on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added one audio message on the page:
                        self.ids.audioMessage_name1.text = self.messageData[str(self.currentMessage)][
                            1]  # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.65,
                                                      "y": 0.5}  # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                        self.ids.button_audioMessage_3.disabled = True
                        self.ids.button_plusIcon.disabled = True
                    elif self.numMessages % 3 == 2:  # modulus used to determine if there are two audio messages on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added two audio messages on the page:
                        self.ids.audioMessage_name1.text = self.messageData[str(self.currentMessage)][
                            1]  # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.audioMessage_name2.text = self.messageData[str(self.currentMessage + 1)][
                            1]  # name of the audio message in the top right icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.17,
                                                      "y": 0.24}  # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                        self.ids.button_audioMessage_3.disabled = False
                        self.ids.button_plusIcon.disabled = True
                    elif self.numMessages % 3 == 0:  # modulus used to determine if there are three audio messages on the final page
                        # code below sets up the icons and buttons for the GUI when the user has already added three audio messages on the page:
                        self.ids.audioMessage_name1.text = self.messageData[str(self.currentMessage)][
                            1]  # name of the audio message in the top left icon is the first item in the tuple
                        self.ids.audioMessage_name2.text = self.messageData[str(self.currentMessage + 1)][
                            1]  # name of the audio message in the top right icon is the first item in the tuple
                        self.ids.audioMessage_name3.text = self.messageData[str(self.currentMessage + 2)][
                            1]  # name of the audio message in the bottom lft icon is the first item in the tuple
                        self.ids.plusIcon.pos_hint = {"x": 0.66,
                                                      "y": 0.24}  # position of plus icon image to create a new audio message
                        self.ids.button_audioMessage_1.disabled = False
                        self.ids.button_audioMessage_2.disabled = False
                        self.ids.button_audioMessage_3.disabled = False
                        self.ids.button_plusIcon.disabled = False
        self.ids.plusIcon.opacity = 1  # sets the opacity of the plus icon (to add more audio messages) to 1 after placing it/them in the correct position on the screen depending on how many audio messages the user has already added


    def addMessage_target(self):
        # instantiates a target view widget which explains how to utilise audio messages
        titleSpaces = '             ' # spaces required to align title text correctly
        descriptionSpaces = '              ' # spaces required to align description text correctly
        # create target view widget with required properties:
        self.targetView = MDTapTargetView(
            widget=self.ids.button_audioMessage_1,
            title_text="{}Add an audio message".format(titleSpaces),
            description_text="{0}You can create personalised\n{0}audio responses which can\n{0}be easily selected in the\n{0}SmartBell app and played by\n{0}"
                             "your SmartBell when a visitor\n{0}comes to the door.".format(descriptionSpaces),
            widget_position="left_top",
            outer_circle_color=(49 / 255, 155 / 255, 254 / 255),
            target_circle_color=(145 / 255, 205 / 255, 241 / 255),
            outer_radius=370,
            title_text_size=33,
            description_text_size=27,
            cancelable=False)

    def openTarget(self):
        # controls the opening of the target view
        if self.targetView.state == "close":  # if the target view is currently closed
            self.targetView.start()  # opens the target view
            self.ids.button_continueIcon.disabled = False  # activates the continue icon button
            animation = Animation(opacity=1, d=0.1)  # automatic animation which gradually increases the opacity of the continue icon image from 0 to 1
            animation.start(self.continueIcon)  # starts the animation of the continue icon image
        else:  # if the target view is currently open
            self.targetView.stop()  # close the target view
            self.ids.button_continueIcon.disabled = True  # deactivates the continue icon button
            animation = Animation(opacity=0, d=0.1)  # automatic animation which gradually decreases the opacity of the continue icon image from 1 to 0
            animation.start(self.continueIcon)  # starts the animation of the continue icon image

    def openMessage(self, buttonNum):
        # opens correct audio message data when user taps on name of an audio message
        if buttonNum == 1:
            self.messageDetails = self.messageData[str(self.currentMessage)]
        elif buttonNum == 2:
            self.messageDetails = self.messageData[str(self.currentMessage + 1)]
        elif buttonNum == 3:
            self.messageDetails = self.messageData[str(self.currentMessage + 2)]
        if self.messageDetails[2] == "Null":
            self.manager.current = "MessageResponses_viewAudio"  # switches to 'MessageResponses_createAudio' GUI
            self.manager.current_screen.__init__()  # initialises the running instance of the 'MessageResponses_createAudio' class
            self.manager.current_screen.messageDetails_init(
                self.messageDetails)  # calls the 'messageDetails_init' method of the running instance of the 'MessageResponses_createAudio' class
        else:
            self.manager.current = "MessageResponses_createText"  # switches to 'MessageResponses_createAudio' GUI
            self.manager.current_screen.__init__()  # initialises the running instance of the 'MessageResponses_createAudio' class
            self.manager.current_screen.messageDetails_init(
                self.messageDetails)  # calls the 'messageDetails_init' method of the running instance of the 'MessageResponses_createAudio' class

    def respondAudio_select(self):
        # called when user selects Respond button when visitor image displayed in mobile app
        self.previewMessages = True
        self.ids.previewMessages.opacity = 1  # changes background image to instruct user to select images

    def respondAudio_preview(self, currentMessage):
        # formats audio message preview displayed when user selects an audio message to be played through doorbell
        messageNum = (self.currentPage - 1) * 3 + currentMessage - 1  # calculates message number so that messageID can be retrieved from json object 'self.messageData'
        self.messageID = self.messageData[str(messageNum)][0]
        self.messageName = self.messageData[str(messageNum)][1]
        self.messageText = self.messageData[str(messageNum)][2]
        if len(self.messageText) < 25:
            self.maxLength = len(self.messageText)
        else:
            self.maxLength = 25
        self.previewMessage_dialog()

    def respondAudio_new(self):
        pass


    def cancelRespond_dialog(self):
        # creates dialog box which asks user to confirm whether they would like to cancel their audio message response after the doorbell has been rung
        self.dialog = MDDialog(
            title="Are you sure you want to cancel your response?",
            auto_dismiss=False,
            type="custom",
            buttons=[MDFlatButton(text="NO", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="YES", md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.cancelRespond)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box


    def cancelRespond(self, instance):
        # called if user indicates that they would like to cancel their audio message response
        self.dialog.dismiss()
        if self.manager.get_screen('VisitorImage').ids.faceName.text == 'Face unknown':
            self.updateFaces_dialog()
        self.manager.current = "Homepage"

    def previewMessage_dialog(self):
        # creates dialog box which displays preview of audio message response before user selects to play message through mobile app
        if self.messageText == "Null":
            text = "[b][i]This is an audio message[/i][/b]" # markup used to increase accessibility and usability
        else:
            text = "[b]Message preview [/b]\n\n[i]" + self.messageText[:self.maxLength] + "[/i]"
        self.dialog = MDDialog(
            title="Play message '{}' through your SmartBell?".format(self.messageName),
            text=text,
            auto_dismiss=False,
            type="custom",
            buttons=[MDFlatButton(text="NO", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="YES!",
                                    on_press=self.transmitMessage)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box


    def transmitMessage(self, instance):
        # transmits details about audio message response to Raspberry Pi over MQTT
        self.dialog.dismiss()
        MQTTPython = autoclass('MQTT') # invoke Objective C class class to transmit audio message
        mqtt = MQTTPython.alloc().init()
        if self.messageText != "Null":
            mqtt.publishData = str(self.messageText)
            mqtt.publishTopic = f"message/text/{self.accountID}"
        else:
            mqtt.publishData = str(self.messageID)
            mqtt.publishTopic = f"message/audio/{self.accountID}"
        mqtt.publish()
        if self.manager.get_screen('VisitorImage').ids.faceName.text == 'Face unknown':
            self.updateFaces_dialog()

    def updateFaces_dialog(self):
        # create dialog box to enable user to input name of visitor if they couldn't be recognised to train facial recognition algorithm
        self.dialog = MDDialog(
            title="Enter visitor's name so SmartBell can identify them next time:",
            auto_dismiss=False,
            type="custom",
            content_cls=DialogContent(),
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="SAVE",
                                    on_press=self.knownFaces_update)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box


    def knownFaces_update(self, instance):
        # update details of identified faces in SQL database
        global faceID
        self.dialog.dismiss()
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the visitor
            if isinstance(object, MDTextField):
                faceName = object.text
        data_knownFaces = {"faceName": faceName, "faceID": faceID}
        requests.post(serverBaseURL + "/update_knownFaces", data_knownFaces)
        self.manager.get_screen('VisitorImage').ids.faceName.text = faceName



class MessageResponses_create(Launch):
    # 'MessageResponses_create' class allows the user to select whether they would like to record their audio message using their voice as the input or type their audio message using the on-screen keyboard as their input. The GUI is created in the kv file.
    pass


class MessageResponses_createAudio(Launch):
    # 'MessageResponses_createAudio' class allows users to record their personalised audio message which can be played through their SmartBell doorbell

    def __init__(self, **kw):
        # loads the images/gifs required to create the GUI for the user to record their audio message
        super().__init__(**kw)
        self.initialRecording = True
        self.recordAudio_static = "SmartBell_audioRecord_static.png"  # loads the static mic image file
        self.recordAudio_listening = "SmartBell_audioRecord_listening.zip"  # loads the zip file used to create the second part of the gif displayed when the user is recording their audio message
        self.recordAudio_loading = "SmartBell_audioRecord_loading.zip"  # loads the zip file used to create the third part of the gif displayed when the user is recording their audio message
        self.recordAudio_end = "SmartBell_audioRecord_end.zip"  # loads the zip file used to create the final part of the gif displayed when the user is recording their audio message
        Clock.schedule_once(
            self.finishInitialising) # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay initialisation

    def finishInitialising(self, dt):
        # applies launch processes which require access to Kivy ids
        self.ids.recordAudio.source = self.recordAudio_static  # sets the source of the image with id 'recordAudio' to the static microphone image
        self.ids.button_recordAudio.disabled = False  # activates the button to record an audio message

    def rerecordAudio(self, messageDetails):
        # called when user selects Record after previewing their audio message recording
        self.messageDetails = messageDetails
        self.initialRecording = False

    def startRecording(self):
        # begins the process of recording the user's audio message
        self.jsonStore.put("localData", initialUse=False, loggedIn=self.loggedIn, accountID=self.accountID,
                           paired=self.paired)
        self.statusUpdate()
        self.recordAudio = RecordAudio()  # instantiates the method which is used to control the recording of the user's audio message
        recordAudio_thread = Thread(target=self.recordAudio.start, args=(),
                                         daemon=False)  # initialises the instance of thread which is used to record the user's audio input
        self.ids.recordAudio.anim_loop = 0  # sets the number of loops of the gif to be played (which uses the zio file 'SmartBell_audioRecord_listening.zip') to infinite as the length of the user's audio message is indeterminate
        self.ids.recordAudio.size_hint = 4, 4
        self.ids.recordAudio.source = self.recordAudio_listening  # changes the source of the image with the id 'recordAudio'
        self.startTime = time.time()  # sets up timer to record how long button to record audio is held for
        recordAudio_thread.start()  # starts the thread instance called 'self.recordAudio_thread'

    def stopRecording(self):
        # terminates the recording of the user's audio message
        self.ids.recordAudio.size_hint = 2, 2
        self.ids.recordAudio.source = self.recordAudio_static  # changes the source of the image with the id 'recordAudio'
        endTime = time.time()  # stops the timer which records how long button to record audio is held for
        if (endTime - self.startTime) <= 1:  # if this audio recording is too short, an error message will be returned
            self.recordAudio.falseStop()  # calls the method which clears the data stored from the recording as the recording was too short and therefore is invalid
            self.ids.snackbar.font_size = 30
            self.ids.snackbar.text = "Press and hold the microphone to speak"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.topHeight =0.13
            self.sleepTime = 3.5
            self.openSnackbar() # calls the method which opens the snackbar to indicate that the audio message recorded was too short
            dismissSnackbar_thread = Thread(target=self.dismissSnackbar, args=(),
                                                 daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
            dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'
        else:  # if the button to record audio is held for more than one second
            self.ids.button_recordAudio.disabled = True  # disables the button to record an audio message
            audioData = self.recordAudio.stop()  # calls the method which terminates the recording of the user's voice input and saves the audio data
            messagePath = join(self.filepath, "audioMessage_tmp.pkl")
            with open(messagePath,
                      "wb") as file:  # create pkl file with name equal to the messageID in write bytes mode
                pickle.dump(audioData,
                            file)  # 'pickle' module serializes the data stored in the Python list object 'audioData' into a byte stream which is stored in pkl file
                file.close()  # closes the file
            self.manager.current = "MessageResponses_viewAudio"  # switches to 'MessageResponses_viewAudio' GUI
            self.manager.current_screen.__init__()  # initialises the running instance of the 'MessageResponses_createAudio' class
            if self.initialRecording == False:
                self.manager.current_screen.messageDetails_init(
                    self.messageDetails)  # calls the 'messageDetails_init' method of the running instance of the 'MessageResponses_createAudio' class

    def helpAudio(self):
        # instructs the user how to record an audio message if they press the 'Help' button
        self.ids.snackbar.font_size = 30
        self.ids.snackbar.text = "Press and hold the microphone to speak"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
        self.topHeight =0.13
        self.sleepTime = 3.5
        self.openSnackbar() # calls the method which opens the snackbar to indicate that the audio message recorded was too short
        dismissSnackbar_thread = Thread(target=self.dismissSnackbar, args=(),
                                             daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
        dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'


class RecordAudio():
    # 'RecordAudio' class allows user to create personalised audio messages using voice input
    def __init__(self, **kw):
        # initialises constant properties for the class
        super().__init__(**kw)
        self.bufferRate = 60  # variables which stores the number of audio buffers recorded per second
        self.audioData = []  # creates a list to store the audio bytes recorded
        self.mic = get_input(callback=self.micCallback, rate=8000, source='default',
                             buffersize=2048)  # initialises the class 'get_input' from the module 'audiostream' with the properties required to ensure the audio is recorded correctly
        print("init")

    def micCallback(self, buffer):
        # called by the class 'get_input' to store recorded audio data (each buffer of audio samples)
        self.audioData.append(buffer)  # appends each buffer (chunk of audio data) to variable 'self.audioData'
        print("buffer")

    def start(self):
        # begins the process of recording the audio data
        self.mic.start()  # starts the method 'self.mic' recording audio data
        Clock.schedule_interval(self.readChunk,
                                1 / self.bufferRate)  # calls the method 'self.readChunk' to read and store each audio buffer (2048 samples) 60 times per second
        print("start")

    def readChunk(self, bufferRate):
        # coordinates the reading and storing of the bytes from each buffer of audio data (which is a chunk of 2048 samples)
        self.mic.poll()  # calls 'get_input(callback=self.mic_callback, source='mic', buffersize=2048)' to read the byte content. This byte content is then dispatched to the callback method 'self.micCallback'
        print("chunk")

    def falseStop(self):
        # terminates the audio recording when the duration of audio recording is less than 1 second
        self.audioData = []  # clears the list storing the audio data
        Clock.unschedule(self.readChunk)  # un-schedules the Clock's execution of 'self.readChunk'
        self.mic.stop()  # stops recording audio

    def stop(self):
        # terminates and saves the audio recording when the recording has been successful
        Clock.unschedule(self.readChunk)  # un-schedules the calling 'self.readChunk'
        self.mic.stop()  # stops recording audio
        return self.audioData


class MessageResponses_view(Launch):
    # 'MessageResponses_view' Class displays the user's names of the user's recorded audio messages

    def __init__(self, **kw):
        self.statusUpdate()
        Screen.__init__(self, **kw) # only initialise the screen as no need to initialise Launch again as this takes user to homepage
        self.audioRename = False

    def messageDetails_init(self, messageDetails):
        # called when changing the content of an audio message (re-recording or re-typing)
        self.messageDetails = messageDetails
        self.messageID = self.messageDetails[0]
        self.messageName = self.messageDetails[1]
        self.messageText = self.messageDetails[2]
        self.initialRecording = False
        self.initialTyping = False
        # if the message is a text message
        if self.messageType == "Text":
            self.ids.messageText.text = self.messageText  # set the text in the text box to the old value of the text
        elif os.path.isfile(join(self.filepath, (
                self.messageID + ".wav"))):  # added to remove old version of audio recording with same messageID (audio file name) stored on app, when user re-records the audio message
            os.remove(join(self.filepath, (self.messageID + ".wav")))

    def nameMessage_dialog(self):
        # allows the user to input the name of the audio message which they recorded/typed
        if (self.initialRecording == False and self.messageType == "Voice") or (
                self.initialTyping == False and self.messageType == "Text"):
            title = "Enter a new name for this audio message or press 'cancel' to keep it named '{}':".format(
                self.messageName)
        else:
            title = "What would you like to name your audio message?"
        self.dialog = MDDialog(
            title=title,
            auto_dismiss=False,
            type="custom",
            content_cls=DialogContent(),  # content class
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="SAVE", md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.nameMessage)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box

    def dismissDialog(self, instance):
        # alters dismissDialog method in inherited Class - polymorphism
        super().dismissDialog(instance)
        if (self.initialRecording == False and self.messageType == "Voice") or (
                self.initialTyping == False and self.messageType == "Text"):
            self.audioMessages_update()

    def nameMessage(self, instance):
        # called when the button 'Save' is tapped on the dialog box which allows the user to input the name of the audio message they recorded/typed
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the audio message they recorded/typed
            if isinstance(object, MDTextField):  # if the object is an MDTextField
                dbData_name = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
                self.messageName = object.text
                dbData_name[
                    "messageName"] = self.messageName  # adds the variable 'object.text' to the dictionary 'dbData_create'
                dbData_name[
                    "accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_create'
                response = requests.post(serverBaseURL + "/verify_messageName",
                                         dbData_name)  # sends post request to 'verify_messageName' route on AWS server to check whether the message name that the user has inputted has already been assigned to one of their audio messages
                if (object.text == "" or object.text == "Null" or response.text == "exists" or len(
                        object.text) > 13):  # if the user has not inputted any text or if the user's input is 'Null' (input used to indicate an audio message' or if the message name is already in use by that user or if the length of the message name is greater than 13 characters
                    xCood = int(
                        instance.pos[0])  # assigns current x coordinate of the 'Save' button to the variable 'xCood'
                    yCood = int(
                        instance.pos[1])  # assigns current y coordinate of the 'Save' button to the variable 'yCood'
                    animation = Animation(pos=((xCood + 7), yCood), t="out_elastic",
                                          d=0.02)  # creates an animation object which moves the 'Save' button to the right
                    animation += Animation(pos=((xCood - 7), yCood), t="out_elastic",
                                           d=0.02)  # adds a sequential step to the animation object which moves the 'Save' button to the left
                    animation += Animation(pos=(xCood, yCood), t="out_elastic",
                                           d=0.02)  # adds a sequential step to the animation object which moves the 'Save' button to its original position
                    animation.start(instance)  # starts the animation instance
                else:  # if the user has inputted a name which is not already in use by that user and is 13 or less characters in length
                    if (self.initialRecording and self.messageType == "Voice") or (
                            self.initialTyping == True and self.messageType == "Text"):  # if this audio message has just been recorded
                        self.messageID = self.createMessageID()  # calls the method which creates a unique messageID for the audio message which the user has created
                    if self.audioRename:  # if the user has played the audio message, then it will have been converted to a wav file already, so this wav file should be renamed with the newly created messageID
                        oldName = join(self.filepath, "audioMessage_tmp.wav")
                        newName = join(self.filepath, (self.messageID + ".wav"))
                        os.rename(oldName, newName)
                    self.dialog.dismiss()  # closes the dialog box
                    self.messageName = object.text  # assigns the text of the MDTextField to the variable 'self.messageName' (the text is the name of the audio message as inputted by the user)
                    self.audioMessages_update()  # calls the method to update the MySQL table 'audioMessages'

    def createMessageID(self):
        # creates a unique messageID for the audio message created by the user
        while True:  # creates an infinite loop
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
            messageID = ''.join(random.choice(chars) for i in range(16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique messageID
            dbData_create = {"messageID": messageID}  # adds the variable 'messageID' to the dictionary 'dbData_create'
            response = requests.post(serverBaseURL + "/verify_messageID",
                                     dbData_create)  # sends post request to 'verify_messageID' route on AWS server to check whether the messageID that has been generated for an audio message does not already exist
            if response.text == "notExists":  # if the messageID does not yet exist
                break  # breaks the infinite loop
            else:
                pass
        return messageID  # returns the unique message ID generated for this audio message

    def deleteMessage(self):
        # deletes user's audio message
        dbData_update = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_update[
            "messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/delete_audioMessages",
                                 dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'


class MessageResponses_viewAudio(MessageResponses_view):
    # 'MessageResponses_viewAudio' Class displays an audio message which the user has already recorded
    def __init__(self, **kw):
        super().__init__(**kw)
        self.messagePath = join(self.filepath, "audioMessage_tmp.pkl") # filepath to store .pkl file of audio bytes for audio message which is not yet saved by user
        self.playbackAudio_gif = "SmartBell_playbackAudio.zip"  # loads the zip file used to create the audio playback gif
        self.playbackAudio_static = "SmartBell_playbackAudio.png"  # loads the image file of the audio playback static image
        self.initialRecording = True
        self.initialTyping = None
        self.messageID = ""
        self.messageType = "Voice"

    def audioMessages_update(self):
        # updates the MySQL table to store the data about the audio message created by the user
        dbData_update = {'messageID': self.messageID, 'messageName': self.messageName, 'messageText': self.messageText, 'accountID': self.accountID, 'initialCreation': str(self.initialRecording)}  # json object which stores the metadata required for the AWS server to update the MySQL database
        response = requests.post(serverBaseURL + "/update_audioMessages",
                                 dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'
        try:  # wav file to be uploaded to AWS only exists if a new audio message has been recorded - else if the audio message name has just been changed, the statement will break
            self.uploadAWS()  # calls the method to upload the audio message data to AWS S3
        except:
            pass
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class

    def uploadAWS(self):
        # sends the data for the audio message recorded by the user as a pkl file to the AWS elastic beanstalk environment, where it is uploaded to AWS s3 using 'boto3' module
        uploadData = {"bucketName": "nea-audio-messages",
                           "s3File": self.messageID}  # creates the dictionary which stores the metadata required to upload the personalised audio message to AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
        # if an audio message with the same messageID already exists, it will be overwritten
        file = {"file": open(self.messagePath,
                             "rb")}  # opens the file to be sent using Flask's 'request' method (which contains the byte stream of audio data) and stores the file in a dictionary
        requests.post(serverBaseURL + "/uploadS3", files=file,
                                 data=uploadData)  # sends post request to 'uploadS3' route on AWS server to upload the pkl file storing the data about the audio message to AWS s3 using 'boto3'
        # This is done because the 'boto3' module cannot be installed on mobile phones so the process of uploading the pkl file to AWS s3 using boto3 must be done remotely on the AWS elastic beanstalk environment
        os.remove(self.messagePath)

    def audioMessage_play(self):
        # allows user to playback the audio message which they have recorded
        if os.path.isfile(join(self.filepath, (self.messageID + ".wav"))):
            fileName = join(self.filepath, self.messageID)
            print("wav on app")
        else:
            if os.path.isfile(self.messagePath):
                with open(self.messagePath, "rb") as file:
                    audioData = pickle.load(file)
                    file.close()  # closes the file
                    self.audioRename = True
                    fileName = join(self.filepath, "audioMessage_tmp")
                    print("pkl on app")
            else:
                fileName = join(self.filepath, self.messageID)
                downloadData = {"bucketName": "nea-audio-messages",
                                     "s3File": self.messageID}  # creates the dictionary which stores the metadata required to download the pkl file of the personalised audio message from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
                response = requests.post(serverBaseURL + "/downloadS3", downloadData)
                audioData = pickle.loads(response.content)  # unpickles the byte string
                print("pkl on AWS")
            messageFile = wave.open(fileName + ".wav", "wb") # load .wav file in write bytes mode
            messageFile.setnchannels(1)  # audiostream module records in single audio channel
            messageFile.setsampwidth(2) # bytes per audio sample
            messageFile.setframerate(8000) # samples recorded per second
            messageFile.writeframes(b''.join(audioData)) # join together each element in the bytes list 'audioData' (each element is an audio buffer)
            messageFile.close()
        messageFile_voice = SoundLoader.load(fileName + ".wav")
        messageFile_voice.play()
        self.ids.playbackAudio.source = self.playbackAudio_gif
        self.audioLength = messageFile_voice.length
        thread_stopGif = Thread(target=self.stopGif, args=(),
                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
        thread_stopGif.start()  # starts the thread which will run in pseudo-parallel to the rest of the program

    def stopGif(self):
        # ends the looping of the playback gif
        time.sleep(self.audioLength)
        self.ids.playbackAudio.source = self.playbackAudio_static

    def tmpAudio_delete(self):
        # deletes the temporary audio file
        if os.path.isfile(self.messagePath):
            os.remove(self.messagePath)


class MessageResponses_createText(MessageResponses_view):
    # 'MessageResponses_createText' Class displays a typed audio message which the user has created
    def __init__(self, **kw):
        super().__init__(**kw)
        self.initialTyping = True
        self.initialRecording = None
        self.messageType = "Text"

    def saveMessage(self):
        # creates dialog box to specify name for typed audio message
        if (len(list((self.ids.messageText.text).strip())) > 80 or len(list((self.ids.messageText.text).strip())) == 0):
            self.ids.snackbar.font_size = 30
            self.ids.snackbar.text = "Sorry, the text you have entered is invalid!\nPlease make sure your message is between\n1 and 80 characters."  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
            self.topHeight =0.13
            self.sleepTime = 3.5
            self.openSnackbar() # calls the method which opens the snackbar to indicate that the audio message recorded was too short
            dismissSnackbar_thread = Thread(target=self.dismissSnackbar, args=(),
                                                 daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
            dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'
        else:
            self.nameMessage_dialog()

    def audioMessages_update(self):
        # updates the MySQL table to store the data about the audio message created by the user
        messageText = self.ids.messageText.text
        #self.statusUpdate() # get latest value for accountID
        dbData_update = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_update[
            "messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        dbData_update[
            "messageName"] = self.messageName  # adds the variable 'messageName' to the dictionary 'dbData_update'
        dbData_update[
            "messageText"] = messageText  # adds the 'null' variable 'fileText' to the dictionary 'dbData_update'
        dbData_update[
            "accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_update'
        dbData_update["initialCreation"] = str(
            self.initialTyping)  # adds the variable 'initialRecording' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/update_audioMessages",
                                 dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'
        self.jsonStore.put("localData", initialUse=False, loggedIn=self.loggedIn, accountID=self.accountID,
                      paired=self.paired)
        self.statusUpdate()  # update launch variables
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class


class VisitorLog(Launch):
    # 'VisitorLog' class displays the details of the visits to the user's doorbell

    def __init__(self, **kw):
        super().__init__(**kw)
        thread = Thread(target=self.schedule)
        thread.start()

    def schedule(self):
        Clock.schedule_once(self.visitorLog)

    def visitorLog(self, dt):
        # creates visitor log
        self.statusUpdate()
        self.get_averageRate()
        self.get_averageTime()
        dbData_accountID = {"accountID": self.accountID}
        self.visitors = requests.post(serverBaseURL + "/get_visitorLog", dbData_accountID).json() # retrieve visitor log details associated with user's account
        for index, visitDetails in enumerate(self.visitors): # iterate through visit details in visitor log
            self.epoch = float(visitDetails[0][6:])
            self.date = time.strftime('%d-%m-%Y, %H:%M:%S', time.gmtime(self.epoch)) # convert epoch time in seconds into actual time/date
            self.faceID = visitDetails[1]
            self.visitID = visitDetails[2]
            self.visitorImage_path = join(self.filepath, self.visitID + '.png')
            self.get_visitorImage() # download visitor image for visit 'visitID'
            if self.faceID != 'NO_FACE': # if face identified for visit
                dbData_faceID = {"faceID": self.faceID}
                result = requests.post(serverBaseURL + "/get_faceName", dbData_faceID).json()
                faceName = result[0]
                self.visitors[index][1] = faceName # replace face ID with face name
            else: # if no face identified
                self.visitors[index][1] = 'No face identified'
            self.visitors[index][2] = self.visitorImage_path # store path to visitor image associated with visit ID
            self.visitors[index] += (self.date,) # append the date to the tuple 'visitors'
        self.visitorsFormatted = list(map(lambda a:(a[0][6:], a[1], a[2], a[3]), self.visitors)) # create array storing required values
        self.displayLog('date')

    def displayLog(self, dateORname):
        # create scrolling list to display visitor log
        self.visitorsSorted = self.mergeSort(self.visitorsFormatted, dateORname) # sort list storing visit details by visitor name or by date of visit
        self.ids.container.clear_widgets() # clear existing visitor log scroll list
        for visit in self.visitorsSorted:
            rowWidget = TwoLineAvatarListItem(text=f"Name: {visit[1]}", secondary_text = f"Date: {visit[3]}") # create row widget with visitor name and date
            rowWidget.add_widget(ImageLeftWidget(source= visit[2])) # add associated visit image to row widget
            self.ids.container.add_widget(rowWidget) # add row widget to scroll list

    def get_visitorImage(self):
        # download visitor images from AWS to display in visitor log
        downloadData = {"bucketName": "nea-visitor-log",
                        "s3File": self.visitID}  # creates the dictionary which stores the metadata required to download the png file of the visitor image from AWS S3 (via the server REST API)
        response = requests.post(serverBaseURL + "/downloadS3",
                                 downloadData)  # request sent to custom REST API, which uses 'boto3' module to attempt to download the visitor image with name 'visitID' from AWS S3
        responseMessage = response.content  # bytes content of message returned by REST API
        time.sleep(0.5)  # time delay to reduce number of requests to AWS API, reducing running costs
        visitorImage_data = responseMessage  # stores visitor image bytes data
        f = open(self.visitorImage_path,'wb')  # opens file to store image bytes (opens in 'wb' format to enable bytes to be written to this file)
        f.write(visitorImage_data)  # writes visitor image bytes data to the file
        f.close()
        time.sleep(0.5)


    def mergeSort(self, array, dateORname):
        # sorts visitor log by criteria specified by user
        if dateORname == 'date':
            index = 1 # specifies index of value in 'array' to be used to sort array
            self.date = True
        else:
            index = 0 # specifies index of value in 'array' to be used to sort array
            self.date = False
        if len(array) > 1: # if array has length greater than 1, continue splitting it
            mid = len(array) // 2 # find middle index of array
            left = array[:mid] # store left half of array elements
            right = array[mid:] # store right half of array elements

            self.mergeSort(left, dateORname) # recursively call the mergesort function on the left of array elements to sort left half
            self.mergeSort(right, dateORname) # recursively call the mergesort function on the right of array elements to sort right half

            # merge and sort left and right array
            i = 0 # left array index
            j = 0 # right array index
            k = 0 # main array index
            while i < len(left) and j < len(right):
                # sort array by comparing and swapping values in tuple at index 'index'
                if left[i][index] < right[j][index]: # value in left array less than value in right array
                    array[k] = left[i] # save value in left index into merged array
                    i += 1 # move to next index in left array
                else: # value in left array greater than or equal to value in right array
                    array[k] = right[j]
                    j += 1 # move to next index in right array
                k += 1 # move to next index in merged array

            # move all remaining values in left array into merged array, as no more values in right array to compare with
            while i < len(left):
                array[k] = left[i]
                i += 1
                k += 1

            # move all remaining values in right array into merged array, as no more values in left array to compare with
            while j < len(right):
                array[k] = right[j]
                j += 1
                k += 1
        return array


    def get_averageRate(self):
        # get average number of visits per day
        dbData_accountID = {"accountID": self.accountID}
        response = requests.post(serverBaseURL + "/get_averageRate", dbData_accountID)
        self.averageRate = str(round(response.json()['result'],1))
        text = f"Average number of visits per day: {str(self.averageRate)} visits"
        self.ids.averageRate.text = text

    def get_averageTime(self):
        # get average time when doorbell is rung
        dbData_accountID = {"accountID": self.accountID}
        response = requests.post(serverBaseURL + "/get_averageTime", dbData_accountID)
        self.averageTime = round(response.json()['result'],2)
        hours = int(self.averageTime) # total number of complete hours
        minutes = (self.averageTime * 60) % 60 # total number of minutes remaining from complete hours
        self.averageTime = str("%02d:%02d" % (hours, minutes)) # zero padding and two decimal places for each number
        text = f"Average time of visit (24hr): {self.averageTime}"
        self.ids.averageTime.text = text


class RingAlert(Launch):
    # 'RingAlert' Class displays a screen with a pulsating doorbell image when the doorbell is rung
    pass


class VisitorImage(Launch):
    # 'VisitorImage' Class displays the image of the visitor when the doorbell is rung

    def viewImage(self):
        # image of visitor and associated name (if identified) displayed in mobile app
        global faceID
        self.statusUpdate()
        dbData_accountID = {"accountID": self.accountID}
        print(self.jsonStore.get('localData'))
        response = requests.post(serverBaseURL + "/latest_visitorLog", dbData_accountID).json()['result']
        if response == 'none':
            self.manager.get_screen(
                'Homepage').ids.snackbar.text = 'No images captured by SmartBell on your account'
            self.manager.current = 'Homepage'
            MDApp.get_running_app().manager.get_screen('Homepage').topHeight = 0.13
            MDApp.get_running_app().manager.get_screen('Homepage').sleepTime = 3
            self.manager.get_screen('Homepage').openSnackbar()  # calls the method which creates the snackbar animation
            thread_dismissSnackbar = Thread(target=self.manager.get_screen('Homepage').dismissSnackbar, args=(),
                                            daemon=False)  # initialises an instance of the 'threading.Thread()' method
            thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
        else:
            visitID = response[0]
            visitorImage_path = join(self.filepath, 'visitorImage.png')
            thread_visitorImage = Thread(target=visitorImage_thread, args=(
            visitID,visitorImage_path))  # thread created so image is downloaded in the background, and so does not delay loading of screen
            thread_visitorImage.setDaemon(True)
            thread_visitorImage.start()
            data_visitID = {"visitID": visitID}
            response = requests.post(serverBaseURL + "/getVisit", data_visitID).json()
            faceID = response[1]
            if faceID != "NO_FACE":  # faceID is set to 'NO_FACE' when a face cannot be detected in the image taken by the doorbell
                data_faceID = {"faceID": str(faceID)}
                faceName = None
                while faceName == None:  # loop until faceID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
                    faceName = requests.post(serverBaseURL + "/view_knownFaces", data_faceID).json()[0]
                if faceName == "":
                    faceName = "Face unknown"
            else:
                faceName = "No face identified"
            self.ids.faceName.text = faceName

    def cancelRespond_dialog(self):
        # creates dialog box which asks user to confirm whether they want to cancel their audio message response after the doorbell has been rung
        self.dialog = MDDialog(
            title="Are you sure you want to cancel your response?",
            auto_dismiss=False,
            type="custom",
            buttons=[MDFlatButton(text="NO", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="YES", md_bg_color=(136 / 255, 122 / 255, 239 / 255, 1),
                                    on_press=self.cancelRespond)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box

    def cancelRespond(self, instance):
        # called if user indicates that they would like to cancel their audio message response
        self.dialog.dismiss()
        if self.ids.faceName.text == 'Face unknown':
            self.updateFaces_dialog()
        self.manager.current = "Homepage"

    def updateFaces_dialog(self):
        # creates dialog box which gives user option to enter name of visitor if they weren't identified by the facial recognition algorithm
        self.dialog = MDDialog(
            title="Enter visitor's name so SmartBell can identify them next time:",
            auto_dismiss=False,
            type="custom",
            content_cls=DialogContent(),
            buttons=[MDFlatButton(text="CANCEL", text_color=((128 / 255), (128 / 255), (128 / 255), 1),
                                  on_press=self.dismissDialog),
                     MDRaisedButton(text="SAVE",
                                    on_press=self.knownFaces_update)])  # creates the dialog box with the required properties for the user to input the name of the audio message recorded/typed
        self.dialog.open()  # opens the dialog box

    def knownFaces_update(self, instance):
        # store details about visitor's face in SQL database
        global faceID
        self.dialog.dismiss()
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the visitor
            if isinstance(object, MDTextField):
                faceName = object.text
        data_knownFaces = {"faceName": faceName, "faceID": faceID}
        requests.post(serverBaseURL + "/update_knownFaces", data_knownFaces)
        self.ids.faceName.text = faceName


class DialogContent(BoxLayout):
    # 'DialogContent' Class contains the standard structure for a Kivy Dialog box
    pass


class MyApp(MDApp):
    # 'MyApp' class is used to create app GUI by building 'layout.kv' file
    def build(self, **kw):
        layout = Builder.load_file("layout.kv")  # loads the 'layout.kv' file
        return layout


def visitorImage_thread(visitID, visitorImage_path):
    # downloads the image of the visitor when the doorbell is rung and displays it in the mobile app
    try:
        for visitorImage in MDApp.get_running_app().manager.get_screen('VisitorImage').ids.visitorImage.children:
            visitorImage.opacity = 0
    except:
        pass
    MDApp.get_running_app().manager.get_screen(
        'VisitorImage').ids.loading.opacity = 1  # reset opacity of image loading gif
    MDApp.get_running_app().manager.get_screen(
        'VisitorImage').ids.faceName.text = "Loading..."  # reset text of visitor image name label

    downloadData = {"bucketName": "nea-visitor-log",
                    "s3File": visitID}  # creates the dictionary which stores the metadata required to download the png file of the visitor image from AWS S3 (via the server REST API)
    responseMessage = b'error'  # message returned by REST API if the  visitor image uploaded by the Raspberry Pi is not yet available on AWS S3
    while responseMessage == b'error':  # while loop continue looping if message returned by REST API is b'error', as visitor image uploaded by the Raspberry Pi is not yet available on AWS S3
        response = requests.post(serverBaseURL + "/downloadS3",
                                 downloadData)  # request sent to custom REST API, which uses 'boto3' module to attempt to download the visitor image with name 'visitID' from AWS S3
        responseMessage = response.content  # bytes content of message returned by REST API
        time.sleep(0.5)  # time delay to reduce number of requests to AWS API, reducing running costs
    visitorImage_data = responseMessage  # stores visitor image bytes data
    f = open(visitorImage_path,
             'wb')  # opens file to store image bytes (opens in 'wb' format to enable bytes to be written to this file)
    f.write(visitorImage_data)  # writes visitor image bytes data to the file
    f.close()
    time.sleep(0.5)
    visitorImage = AsyncImage(source=visitorImage_path,
                              pos_hint={"center_x": 0.5,
                                        "center_y": 0.53})  # AsyncImage loads image as background thread, so doesn't hold up running of program if there is a delay in loading the image
    visitorImage.reload()
    MDApp.get_running_app().manager.get_screen('VisitorImage').ids.visitorImage.add_widget(
        visitorImage)  # accesses screen ids of 'VisitorImage' screen and adds the visitor image as a widget to a nested Kivy float layout MDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 0 # set opacity of image loading gif to zero as image is loaded and displayed
    MDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 0 # set opacity of image loading gif to zero as image is loaded and displayed


def createThread_ring(accountID, filepath):
    # interfaces with Objective C class 'MQTT' to create client which will receive message when doorbell rung
    MQTTPython = autoclass(
        'MQTT') # autoclass used to load Objective-C class 'MQTT' and create a Python wrapper around it
    mqtt = MQTTPython.alloc().init() # instance of the Objective-C 'MQTT' class created
    mqtt.ringTopic = f"ring/{accountID}" # the Objective-C property 'ringTopic' is assigned
    mqtt.connect()  # call Objective-C method which connects to the MQTT broker
    visitorImage_path = join(filepath, 'visitorImage.png') # path to store visitor image on mobile app
    thread_ring = Thread(target=ringThread,args=(mqtt, visitorImage_path)) # create thread which checks status of Objective-C property 'messageReceived_ring'
    thread_ring.start() # start the thread
    return


def createThread_visit(visitID):
    # creates thread which downloads visitor image from AWS S3 storage
    thread_visit = Thread(target=visitThread, args=(visitID,))
    thread_visit.start()


def ringThread(mqtt, visitorImage_path):
    # checks status of Objective C class attributes to verify whether MQTT message indicating that doorbell has been rung is received
    while True:
        if mqtt.messageReceived_ring == 1: # if message received on topic 'ring/accountID' by Objective-C MQTT session instance (i.e. SmartBell doorbell rung)
            try:  # runs successfully if visitor image already exists on app
                for visitorImage in MDApp.get_running_app().manager.get_screen(
                        'VisitorImage').ids.visitorImage.children:
                    # 'visitorImage' is a nested Kivy float layout, whose children are images of the visitor
                    visitorImage.opacity = 0  # set the opacity of each existing vistor image to 0, so that the previous visitor image is not shown
            except:  # if visitor image doesn’t already exist on app
                pass
            mqtt.messageReceived_ring = 0  # value of 'messageReceived_ring' must be reset to 0 so that new messages can be detected in Python code
            mqtt.vibratePhone()  # calls Objective-C method to vibrate mobile spacespacespMDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 1 # reset opacity of image loading gif          spacespacespMDApp.get_running_app().manager.get_screen('VisitorImage').ids.faceName.text = "Loading..." # reset text of visitor image name label
            MDApp.get_running_app().manager.get_screen(
                'VisitorImage').ids.loading.opacity = 1  # reset opacity of image loading gif
            MDApp.get_running_app().manager.get_screen(
                'VisitorImage').ids.faceName.text = "Loading..."  # reset text of visitor image name label
            MDApp.get_running_app().manager.current = "RingAlert"  # open Kivy screen to notify user that the doorbell has been rung
            visitID = str(
                mqtt.messageData.UTF8String())  # decode message published to topic 'ring/accountID' by Raspberry Pi doorbell
            createThread_visit(visitID) # visit thread only called once doorbell is rung to reduce energy usage.
            downloadData = {"bucketName": "nea-visitor-log",
                            "s3File": visitID}  # creates the dictionary which stores the metadata required to download the png file of the visitor image from AWS S3 (via the server REST API)
            responseMessage = b'error'  # message returned by REST API if the  visitor image uploaded by the Raspberry Pi is not yet available on AWS S3
            while responseMessage == b'error':  # while loop continue looping if message returned by REST API is b'error', as visitor image uploaded by the Raspberry Pi is not yet available on AWS S3
                response = requests.post(serverBaseURL + "/downloadS3",
                                         downloadData)  # request sent to custom REST API, which uses 'boto3' module to attempt to download the visitor image with name 'visitID' from AWS S3
                responseMessage = response.content  # bytes content of message returned by REST API
                time.sleep(0.5)  # time delay to reduce number of requests to AWS API, reducing running costs
            visitorImage_data = responseMessage  # stores visitor image bytes data
            f = open(visitorImage_path,
                     'wb')  # opens file to store image bytes (opens in 'wb' format to enable bytes to be written to this file)
            f.write(visitorImage_data)  # writes visitor image bytes data to the file
            f.close()
            time.sleep(0.5)
            MDApp.get_running_app().manager.current = "VisitorImage"
            visitorImage = AsyncImage(source=visitorImage_path,
                                      pos_hint={"center_x": 0.5,
                                                "center_y": 0.53}) # AsyncImage loads image as background thread, so doesn't hold up running of program if there is a delay in loading the image
            visitorImage.reload()
            mqtt.notifyPhone()  # calls Objective-C method to play notification sound through mobile phone
            MDApp.get_running_app().manager.get_screen('VisitorImage').ids.visitorImage.add_widget(
                visitorImage)  # accesses screen ids of 'VisitorImage' screen and adds the visitor image as a widget to a nested Kivy float layout MDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 0 # set opacity of image loading gif to zero as image is loaded and displayed
            MDApp.get_running_app().manager.get_screen(
                'VisitorImage').ids.loading.opacity = 0  # set opacity of image loading gif to zero as image is loaded and displayed
        else:
            time.sleep(3)  # reduce energy usage of mobile as checking status of 'messageReceived_ring' less frequently


def visitThread(visitID):
    # download visitor image from latest ring of doorbell and display in mobile app
    global faceID
    while True:
        data_visitID = {"visitID": visitID}
        response = None
        while response == None:  # loop until visitID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
            response = requests.post(serverBaseURL + "/getVisit", data_visitID).json()
            time.sleep(1)
        faceID = response[1]
        if faceID != "NO_FACE":  # faceID is set to 'NO_FACE' when a face cannot be detected in the image taken by the doorbell
            data_faceID = {"faceID": str(faceID)}
            faceName = None
            while faceName == None:  # loop until faceID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
                faceName = requests.post(serverBaseURL + "/view_knownFaces", data_faceID).json()[0]
            if faceName == "":
                faceName = "Face unknown"
        else:
            faceName = "No face identified"
        MDApp.get_running_app().manager.get_screen('VisitorImage').ids.faceName.text = faceName
        break


def pairThread(accountID, id, pairing, jsonStore):
    # checks pairing status between mobile app and doorbell
    start_time = time.time()
    dbData_id = {'id': id}
    MDApp.get_running_app().manager.get_screen('Homepage').topHeight = 0.13
    MDApp.get_running_app().manager.get_screen('Homepage').sleepTime = 5
    while True:
        response = (requests.post(serverBaseURL + "/verifyPairing", dbData_id).json())[
            'result']  # sends post request to 'verifyAccount' route on AWS server to check whether the email address inputted is already associated with an account
        if response == accountID and pairing == True:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = f"Successfully paired with SmartBell '{id}'!"
            MDApp.get_running_app().manager.get_screen('Homepage').openSnackbar()
            loggedIn = jsonStore.get("localData")["loggedIn"]
            accountID = jsonStore.get("localData")["accountID"]
            jsonStore.put("localData", initialUse=False, loggedIn=loggedIn, accountID=accountID, paired=id)
            break
        elif response == '' and pairing == False:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = f"Successfully unpaired from SmartBell '{id}'"
            MDApp.get_running_app().manager.get_screen('Homepage').openSnackbar()
            break
        elif response != accountID and response != None and response != '' and pairing == True:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = 'Error pairing SmartBell. Please ensure you\ninput the correct name for your SmartBell'
            MDApp.get_running_app().manager.get_screen('Homepage').openSnackbar()
            break
        elif time.time() - start_time > 60:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = 'Error pairing SmartBell. Please ensure you\ninput the correct name for your SmartBell'
            MDApp.get_running_app().manager.get_screen('Homepage').openSnackbar()
            break
        time.sleep(1)
    thread_dismissSnackbar = Thread(target=MDApp.get_running_app().manager.get_screen('Homepage').dismissSnackbar, args=(),
                                    daemon=False)  # initialises an instance of the 'threading.Thread()' method
    thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program


if __name__ == "__main__":  # when the program is launched, if the name of the file is the main program (i.e. it is not a module being imported by another file) then this selection statement is True
    MyApp().run()  # the run method is inherited from the 'MDApp' class which is inherited by the class 'MyApp'



