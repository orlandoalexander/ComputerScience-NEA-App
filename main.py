import os
os.environ[
    'KIVY_AUDIO'] = 'avplayer'  # control the kivy environment to ensure audio input can be accepted following audio output

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.taptargetview import MDTapTargetView
from kivymd.uix.button import MDFlatButton, MDRaisedButton
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
    # 'Launch' class serves to coordinate the correct launch screen for the mobile app depending on the current status of the app

    def __init__(self, **kw):
        super().__init__(**kw)
        Launch.statusUpdate(self)
        Clock.schedule_once(
            self.finishInitialising)  # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisationas the instantiation results in 1 of 3 methods (Homepage(), signIn() or signUp()) being called, each of which requires access to Kivy ids to create the GUI

    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation
        if self.loggedIn == True:
            createThread_ring(self.accountID, self.filepath)
            # connect to MQTT broker to receive messages when visitor presses doorbell as already logged in
            self.manager.transition = NoTransition()
            self.manager.current = "Homepage"  # if the user is already logged in, then class 'Homepage' is called to allow the user to navigate the app

        elif self.initialUse == True:
            self.manager.transition = NoTransition()
            self.manager.current = "SignUp"

        else:
            self.manager.transition = NoTransition()
            self.manager.current = "SignIn"

    def statusUpdate(self):
        self.filepath = MDApp.get_running_app().user_data_dir
        jsonFilename = join(self.filepath,
                                 "jsonStore.json")  # if file name already exists, it is assigned to 'self.filename'. If filename doesn't already exist, file is created locally on the mobile phone
        # the 'join' class is used to create a single path name to the new file "self.jsonStore.json"
        self.jsonStore = JsonStore(jsonFilename)  # wraps the filename as a json object to store data locally on the mobile phone
        if not self.jsonStore.exists("localData"):
            self.jsonStore.put("localData", initialUse=True, loggedIn=False, accountID="", paired=False)
        self.initialUse = self.jsonStore.get("localData")[
            "initialUse"]  # variable which indicates that the app is running for the first time on the user's mobile
        self.loggedIn = self.jsonStore.get("localData")["loggedIn"]
        self.paired = self.jsonStore.get("localData")["paired"]
        self.accountID = self.jsonStore.get("localData")["accountID"]
        print('logged in:', self.loggedIn)

    def dismissDialog(self, instance):
        # method which is called when 'Cancel' is tapped on the dialog box
        self.dialog.dismiss()  # closes the dialog box

    def openSnackbar(self):
        # method which controls the opening animation of the snackbar
        animation = Animation(pos_hint={"center_x": 0.5, "top": self.topHeight},
                              d=0.03)  # end properties of the snackbar animation's opening motion
        animation.start(self.ids.snackbar)  # executes the opening animation

    def dismissSnackbar(self):
        # method which controls the closing animation of the snackbar
        time.sleep(self.sleepTime)  # delay before snackbar is closed
        animation = Animation(pos_hint={"center_x": 0.5, "top": 0},
                              d=0.03)  # end properties of the snackbar animation's closing motion
        animation.start(self.ids.snackbar)  # executes the closing animation

class Homepage(Launch):

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.paired == False:
            title = f"Enter the name of the SmartBell which you would like to pair with:"
            self.pairDialog(title)
        else:
            self.piID= self.paired
            self.alreadyPaired_dialog()

    def account(self):
        Launch.statusUpdate(self)
        if self.loggedIn == True:
            self.signOut_dialog()
        else:
            self.manager.current = "SignIn"

    def signOut(self, instance):
        self.dialog.dismiss()
        self.loggedIn = False
        self.accountID = ''
        self.paired = False
        self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=self.loggedIn, accountID=self.accountID, paired=self.paired)
        self.manager.current = "SignIn"

    def signOut_dialog(self):
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
        self.dialog.dismiss()  # closes the dialog box
        title = f"Enter the name of the SmartBell which you would like to pair with. Alternatively, enter 'unpair' to unpair from SmartBell '{self.piID}':"
        self.pairDialog(title)

    def pair(self, instance):
        self.dialog.dismiss()
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the audio message they recorded/typed
            if isinstance(object, MDTextField):  # if the object is an MDTextField
                newID = object.text
        if newID.lower() == 'unpair':
            self.jsonStore.put("localData", initialUse=self.initialUse, loggedIn=self.loggedIn, accountID=self.accountID,
                          paired=False)
            Launch.statusUpdate(self)  # update launch variables
            publishData = ""
            id = self.piID
            pairing = False
            pair_thread = Thread(target=pairThread, daemon=True, args=(self.accountID, id, pairing, self.jsonStore))
            pair_thread.start()
        else:
            self.piID= newID
            publishData = str(self.accountID)
            dbData_id = {'id': self.piID}
            response = (requests.post(serverBaseURL + "/checkPairing", dbData_id)).text
            if response == 'notExists':
                self.ids.snackbar.text = f"No SmartBell with the name '{self.piID}' exists!\n"
                self.topHeight =0.095
                self.sleepTime = 5
                self.openSnackbar() # calls the method which creates the snackbar animation
                thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
                thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
            elif response == 'exists':
                pairing = True
                pair_thread = Thread(target=pairThread, daemon=True, args=(self.accountID, self.piID, pairing, self.jsonStore))
                pair_thread.start()
        MQTT = autoclass('MQTT')
        mqtt = MQTT.alloc().init()
        mqtt.publishData = publishData
        mqtt.publishTopic = f"id/{self.piID}"
        mqtt.publish()


class SignUp(Launch):  # launch first to avoid MRO issue - change order to get error log
    # 'SignUp' class allows user to create an account

    def createAccount(self):
        # method called when user taps the Sign Up button
        self.firstName_valid = False  # variable which indicates that a valid value has been inputted by the user
        self.surnameValid = False  # variable which indicates that a valid value has been inputted by the user
        self.emailValid = False  # variable which indicates that a valid value has been inputted by the user
        self.passwordValid = False  # variable which indicates that a valid value has been inputted by the user
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
            if re.search("[@]", email) and re.search("[.]",
                                                     email):  # checks that inputted email contains '@' symbol and '.' to verify the email address as a valid email format
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
                self.passwordValid = True  # variable which indicates that a valid value has been inputted by the user
                if self.firstName_valid and self.surnameValid and self.emailValid and self.passwordValid:  # checks if all the data values have been inputted and are valid
                    self.createAccountID()  # method called to create a unique accountID for the user
                else:
                    pass
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
        self.topHeight = 0.095 # snackbar properties
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
                                     self.dbData_update)  # sends post request to 'updateUsers' route on AWS server with user's inputted data to be stored in the database
            if response.text == "error":  # if an error occurs when adding the user's data into the 'users' table
                self.ids.snackbar.text = "Error creating account. Please try again later"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
                self.ids.snackbar.font_size = 30
                self.openSnackbar() # calls the method which creates the snackbar animation
                thread_dismissSnackbar = Thread(target=self.dismissSnackbar, args=(),
                                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
                thread_dismissSnackbar.start()  # starts the thread which will run in pseudo-parallel to the rest of the program
            else:

                self.jsonStore.put("localData", initialUse=self.initialUse,
                              loggedIn=True, accountID=self.accountID,
                              paired=self.paired)  # updates json object to reflect that user has successfully created an account
                print(self.jsonStore.get('localData'))
                Launch.statusUpdate(self)  # update launch variables

                # connect to MQTT broker to receive messages when visitor presses doorbell as now logged in and have unique accountID

                createThread_ring(self.accountID, self.filepath)

                self.manager.transition = NoTransition()  # creates a cut transition type
                self.manager.current = "Homepage"  # switches to 'Homepage' GUI
                self.manager.current.__init__()



class SignIn(Launch):
    # 'SignIn' class allows users to log into their account

    def signIn(self):
        # method called when user taps the Sign In button
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
            self.hashedPassword = (hashlib.new("sha3_256",
                                               self.password.encode())).hexdigest()  # creates a hash of the user's password so that it can be compared to the hashed version stored on the database
            # the hashing algorithm SHA3-256 is used by the 'hashlib' module to encrypt the UTF-8 encoded version of
            # the password (the method 'encode()' UTF-8 encodes the plaintext password) the method 'hexdigest()'
            # returns the hex value of the hashed password that has been created
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
            Launch.statusUpdate(self)  # update launch variables

            # connect to MQTT broker to receive messages when visitor presses doorbell as now logged in

            createThread_ring(self.accountID, self.filepath)
            self.manager.transition = NoTransition()  # creates a cut transition type
            self.manager.current = "Homepage"  # switches to 'Homepage' GUI


class MessageResponses_add(Launch):
    # 'MessageResponses_add' class allows user to add audio response messages to be played through the doorbell.

    def __init__(self, **kw):
        # assigns the constants which are used in the class and gets the data on existing audio messages
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
        Clock.schedule_once(
            self.finishInitialising)  # Kivy rules are not applied until the original Widget (MessageResponses_add) has finished instantiating, so must delay the initialisation
        # as the instantiation results in 1 of 2 methods (darkenImage() or audioMessage_create()) being called,
        # each of which requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed

    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation
        # as the instantiation results in 1 of 2 methods (darkenImage() or audioMessage_create()) being called, each of which requires access to Kivy ids to create the GUI
        # and this is only possible if the instantiation is delayed.
        if self.initialUse == True and self.numMessages == 0:
            self.ids.pulsingCircle.opacity = 1
        try:
            self.targetView.stop()  # close the target view
        except:
            pass
        self.audioMessage_create(1, 3)


    def audioMessage_create(self, currentPage, currentMessage):
        # method which displays the user's current audio messages and allows users to create new personalised audio messages which can be played through the doorbell
        if self.numMessages == 0:  # if the user has not yet recorded any audio messages
            self.ids.plusIcon.pos_hint = {"x": 0.17, "y": 0.5}  # sets the position for the plus icon
            self.ids.button_audioMessage_1.disabled = False  # activates the button to open the target view widget
            self.addMessage_target()  # calls the method which opens the target view widget which explains to the user what a personalised audio message is
        else:  # if the user has already added a personalised audio message
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
        # instantiates a target view widget which is displayed on the first use of the app to explain to the user what it means to add an audio message
        self.targetView = MDTapTargetView(
            widget=self.ids.button_audioMessage_1,
            title_text="             Add an audio message",
            description_text="              You can create personalised\n              audio responses which can\n              be easily selected in the\n              SmartBell app and played by\n              "
                             "your SmartBell when a visitor\n              comes to the door.",
            widget_position="left_top",
            outer_circle_color=(49 / 255, 155 / 255, 254 / 255),
            target_circle_color=(145 / 255, 205 / 255, 241 / 255),
            outer_radius=370,
            title_text_size=33,
            description_text_size=27,
            cancelable=False
        )  # creates the target view widget with the required properties

    def openTarget(self):
        # method which controls the opening of the target view
        self.ids.pulsingCircle.opacity = 0
        if self.targetView.state == "close":  # if the target view is currently closed
            self.targetView.start()  # opens the target view
            self.ids.button_continueIcon.disabled = False  # activates the continue icon button
            animation = Animation(opacity=1,
                                  d=0.1)  # automatic animation which gradually increases the opacity of the continue icon image from 0 to 1
            animation.start(self.continueIcon)  # starts the animation of the continue icon image
        else:  # if the target view is currently open
            self.targetView.stop()  # close the target view
            self.ids.button_continueIcon.disabled = True  # deactivates the continue icon button
            animation = Animation(opacity=0,
                                  d=0.1)  # automatic animation which gradually decreases the opacity of the continue icon image from 1 to 0
            animation.start(self.continueIcon)  # starts the animation of the continue icon image

    def openMessage(self, buttonNum):
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
        self.previewMessages = True
        self.ids.previewMessages.opacity = 1  # changes background image to instruct user to select images

    def respondAudio_preview(self, currentMessage):
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
        print("Create new audio message")
        # user can create new audio message

    def cancelRespond_dialog(self):
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
        self.dialog.dismiss()
        if self.manager.get_screen('VisitorImage').ids.faceName.text == 'Face unknown':
            self.updateFaces_dialog()
        self.manager.current = "Homepage"

    def previewMessage_dialog(self):
        # markup used to increase accessibility and usability
        if self.messageText == "Null":
            text = "[b][i]This is an audio message[/i][/b]"
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
        self.dialog.dismiss()
        MQTT = autoclass('MQTT') # invoke with name of class
        mqtt = MQTT.alloc().init()
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
        # markup used to increase accessibility and usability
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
            self.finishInitialising)  # Kivy rules are not applied until the original Widget (MessageResponses_createAudio) has finished instantiating, so must delay the initialisation
        # as the instantiation requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed

    def finishInitialising(self, dt):
        # Kivy rules are not applied until the original Widget (Launch) has finished instantiating, so must delay the initialisation
        # as the instantiation requires access to Kivy ids to create the GUI and this is only possible if the instantiation is delayed
        self.ids.recordAudio.source = self.recordAudio_static  # sets the source of the image with id 'recordAudio' to the static microphone image
        self.ids.button_recordAudio.disabled = False  # activates the button to record an audio message

    def rerecordAudio(self, messageDetails):
        self.messageDetails = messageDetails
        self.initialRecording = False

    def startRecording(self):
        # method which begins the process of recording the user's audio message

        self.recordAudio = RecordAudio()  # instantiates the method which is used to control the recording of the user's audio message
        recordAudio_thread = Thread(target=self.recordAudio.start, args=(),
                                         daemon=False)  # initialises the instance of thread which is used to record the user's audio input
        self.ids.recordAudio.anim_loop = 0  # sets the number of loops of the gif to be played (which uses the zio file 'SmartBell_audioRecord_listening.zip') to infinite as the length of the user's audio message is indeterminate
        self.ids.recordAudio.size_hint = 4, 4
        self.ids.recordAudio.source = self.recordAudio_listening  # changes the source of the image with the id 'recordAudio'
        self.startTime = time.time()  # sets up timer to record how long button to record audio is held for
        recordAudio_thread.start()  # starts the thread instance called 'self.recordAudio_thread'

    def stopRecording(self):
        # method which terminates the recording of the user's audio message
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
                            file)  # 'pickle' module serializes the data stored in the object (list) 'audioData' into a byte stream which is stored in pkl file
                file.close()  # closes the file
            self.manager.current = "MessageResponses_viewAudio"  # switches to 'MessageResponses_viewAudio' GUI
            self.manager.current_screen.__init__()  # initialises the running instance of the 'MessageResponses_createAudio' class
            if self.initialRecording == False:
                self.manager.current_screen.messageDetails_init(
                    self.messageDetails)  # calls the 'messageDetails_init' method of the running instance of the 'MessageResponses_createAudio' class

    def helpAudio(self):
        # method which instructs the user how to record an audio message if they press the 'Help' button
        self.ids.snackbar.font_size = 30
        self.ids.snackbar.text = "Press and hold the microphone to speak"  # creates specific text for the generic Label which is used as a snackbar in a varity of scenarios in the app
        self.topHeight =0.13
        self.sleepTime = 3.5
        self.openSnackbar() # calls the method which opens the snackbar to indicate that the audio message recorded was too short
        dismissSnackbar_thread = Thread(target=self.dismissSnackbar, args=(),
                                             daemon=False)  # initialises an instance of the thread which closes the snackbar after 3.5 seconds.
        dismissSnackbar_thread.start()  # starts the thread 'self.dismissSnackbar_thread'


class RecordAudio():
    # 'recordAudio' class allows user to create personalised audio messages using voice input
    def __init__(self, **kw):
        # initialises constant properties for the class
        super().__init__(**kw)
        self.sampleRate = 60  # variables which stores the number of audio samples recorded per second
        self.audioData = []  # creates a list to store the audio bytes recorded
        self.mic = get_input(callback=self.micCallback, rate=8000, source='default',
                             buffersize=2048)  # initialises the method 'get_input' from the module 'audiostream' with the properties required to ensure the audio is recorded correctly
        print("init")

    def micCallback(self, buffer):
        # method which is called by the method 'get_input' to store recorded audio data (each buffer of audio samples)
        self.audioData.append(buffer)  # appends each buffer (chunk of audio data) to variable 'self.audioData'
        print("buffer")

    def start(self):
        # method which begins the process of recording the audio data
        self.mic.start()  # starts the method 'self.mic' recording audio data
        Clock.schedule_interval(self.readChunk,
                                1 / self.sampleRate)  # calls the method 'self.readChunk' to read and store each audio buffer (2048 samples) 60 times per second
        print("start")

    def readChunk(self, sampleRate):
        # method which coordinates the reading and storing of the bytes from each buffer of audio data (which is a chunk of 2048 samples)
        self.mic.poll()  # calls 'get_input(callback=self.mic_callback, source='mic', buffersize=2048)' to read the byte content. This byte content is then dispatched to the callback method 'self.micCallback'
        print("chunk")

    def falseStop(self):
        # method which terminates the audio recording when the duration of audio recording is less than 1 second
        self.audioData = []  # clears the list storing the audio data
        Clock.unschedule(self.readChunk)  # un-schedules the Clock's rythmic execution of the 'self.readChunk' callback
        self.mic.stop()  # stops recording audio

    def stop(self):
        # method which terminates and saves the audio recording when the recording has been successful
        Clock.unschedule(self.readChunk)  # un-schedules the Clock's rythmic execution of the 'self.readChunk' callback
        self.mic.stop()  # stops recording audio
        return self.audioData


class MessageResponses_view(Launch):

    def __init__(self, **kw):
        Launch.statusUpdate(self)
        Screen.__init__(self, **kw) # only initialise the screen as no need to initialise Launch again as this takes user to homepage
        self.audioRename = False

    def messageDetails_init(self, messageDetails):
        # called when changing the content of an audio message (re-recording or re-typing)
        messageDetails = messageDetails
        self.messageID = messageDetails[0]
        self.messageName = messageDetails[1]
        self.messageText = messageDetails[2]
        self.initialRecording = False
        self.initialTyping = False
        # if the message is a text message
        if self.messageType == "Text":
            self.ids.messageText.text = self.messageText  # set the text in the text box to the old value of the text
        elif os.path.isfile(join(self.filepath, (
                self.messageID + ".wav"))):  # added to remove old version of audio recording with same messageID (audio file name) stored on app, when user re-records the audio message
            os.remove(join(self.filepath, (self.messageID + ".wav")))

    def nameMessage_dialog(self):
        # method which allows the user to input the name of the audio message which they recorded/typed
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
        # overrides dismissDialog method in inherited Class - polymorphism
        super().dismissDialog(instance)
        if (self.initialRecording == False and self.messageType == "Voice") or (
                self.initialTyping == False and self.messageType == "Text"):
            self.audioMessages_update()

    def nameMessage(self, instance):
        # method which is called when the button 'Save' is tapped on the dialog box which allows the user to input the name of the audio message they recorded/typed
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
        dbData_create = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        while True:  # creates an infinite loop
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits  # creates a concatenated string of all the uppercase and lowercase alphabetic characters and all the digits (0-9)
            messageID = ''.join(random.choice(chars) for i in range(
                16))  # the 'random' module randomly selects 16 characters from the string 'chars' to form the unique messageID
            dbData_create[
                "messageID"] = messageID  # adds the variable 'messageID' to the dictionary 'dbData_create'
            response = requests.post(serverBaseURL + "/verify_messageID",
                                     dbData_create)  # sends post request to 'verify_messageID' route on AWS server to check whether the messageID that has been generated for an audio message does not already exist
            if response.text == "notExists":  # if the messageID does not yet exist
                break  # breaks the infinite loop
            else:
                pass
        return messageID  # returns the unique message ID generated for this audio message

    def deleteMessage(self):
        dbData_update = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_update[
            "messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/delete_audioMessages",
                                 dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'


class MessageResponses_viewAudio(MessageResponses_view):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.messagePath = join(self.filepath, "audioMessage_tmp.pkl")
        self.playbackAudio_gif = "SmartBell_playbackAudio.zip"  # loads the zip file used to create the audio playback gif
        self.playbackAudio_static = "SmartBell_playbackAudio.png"  # loads the image file of the audio playback static image
        self.initialRecording = True
        self.initialTyping = None
        self.messageID = ""
        self.messageType = "Voice"

    def audioMessages_update(self):
        # method which updates the MySQL table to store the data about the audio message created by the user
        dbData_update = {}  # dictionary which stores the metadata required for the AWS server to make the required query to the MySQL database
        dbData_update[
            "messageID"] = self.messageID  # adds the variable 'messageID' to the dictionary 'dbData_update'
        dbData_update[
            "messageName"] = self.messageName  # adds the variable 'messageName' to the dictionary 'dbData_update'
        dbData_update[
            "messageText"] = "Null"  # adds the 'null' variable 'fileText' to the dictionary 'dbData_update'
        dbData_update[
            "accountID"] = self.accountID  # adds the variable 'accountID' to the dictionary 'dbData_update'
        dbData_update["initialCreation"] = str(
            self.initialRecording)  # adds the variable 'initialRecording' to the dictionary 'dbData_update'
        response = requests.post(serverBaseURL + "/update_audioMessages",
                                 dbData_update)  # sends post request to 'update_audioMessages' route on AWS server to insert the data about the audio message which the user has created into the MySQL table 'audioMessages'
        try:  # wav file to be uploaded to AWS only exists if a new audio message has been recorded - else if the audio message name has just been changed, the statement will break
            self.uploadAWS()  # calls the method to upload the audio message data to AWS S3
        except:
            pass
        self.jsonStore.put("localData", initialUse=False, loggedIn=self.loggedIn, accountID=self.accountID,
                      paired=self.paired)
        Launch.statusUpdate(self)  # update launch variables
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class

    def uploadAWS(self):
        # method which sends the data for the audio message recorded by the user as a pkl file to the AWS elastic beanstalk environment, where it is uploaded to AWS s3 using 'boto3' module
        uploadData = {"bucketName": "nea-audio-messages",
                           "s3File": self.messageID}  # creates the dictionary which stores the metadata required to upload the personalised audio message to AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
        # if an audio message with the same messageID already exists, it will be overwritten
        file = {"file": open(self.messagePath,
                             "rb")}  # opens the file to be sent using Flask's 'request' method (which contains the byte stream of audio data) and stores the file in a dictionary
        response = requests.post(serverBaseURL + "/uploadS3", files=file,
                                 data=uploadData)  # sends post request to 'uploadS3' route on AWS server to upload the pkl file storing the data about the audio message to AWS s3 using 'boto3'
        # This is done because the 'boto3' module cannot be installed on mobile phones so the process of uploading the pkl file to AWS s3 using boto3 must be done remotely on the AWS elastic beanstalk environment
        os.remove(self.messagePath)

    def audioMessage_play(self):
        # method which allows user to playback the audio message which they have recorded

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
                audioData = response.content
                audioData = pickle.loads(response.content)  # unpickles the byte string
                print("pkl on AWS")
            messageFile = wave.open(fileName + ".wav", "wb")
            messageFile.setnchannels(1)  # change to 1 for audio stream module
            messageFile.setsampwidth(2)
            messageFile.setframerate(8000)  # change to 8000 for audio stream module
            messageFile.writeframes(b''.join(audioData))
            messageFile.close()
        messageFile_voice = SoundLoader.load(fileName + ".wav")
        messageFile_voice.play()
        self.ids.playbackAudio.source = self.playbackAudio_gif
        self.audioLength = messageFile_voice.length
        thread_stopGif = Thread(target=self.stopGif, args=(),
                                     daemon=False)  # initialises an instance of the 'threading.Thread()' method
        thread_stopGif.start()  # starts the thread which will run in pseudo-parallel to the rest of the program

    def stopGif(self):
        time.sleep(self.audioLength)
        self.ids.playbackAudio.source = self.playbackAudio_static

    def tmpAudio_delete(self):
        if os.path.isfile(self.messagePath):
            os.remove(self.messagePath)


class MessageResponses_createText(MessageResponses_view):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.initialTyping = True
        self.initialRecording = None
        self.messageType = "Text"

    def saveMessage(self):
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
        # method which updates the MySQL table to store the data about the audio message created by the user
        messageText = self.ids.messageText.text
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
        Launch.statusUpdate(self)  # update launch variables
        self.manager.transition = NoTransition()  # creates a cut transition type
        self.manager.current = "MessageResponses_add"  # switches to 'MessageResponses_add' GUI
        self.manager.current_screen.__init__()  # creates a new instance of the 'MessageResponses_add' class


class VisitorLog(Launch):
    pass


class RingAlert(Launch):
    pass


class VisitorImage(Launch):

    def viewImage(self):
        global faceID
        dbData_accountID = {"accountID": self.accountID}
        response = requests.post(serverBaseURL + "/latest_visitorLog", dbData_accountID).json()['result']
        if response == 'none':
            self.manager.get_screen(
                'Homepage').ids.snackbar.text = 'No images captured by SmartBell on your account\n'
            self.manager.current = 'Homepage'
            self.manager.get_screen('Homepage').snackbar()
        else:
            visitID = response[0]
            thread_visitorImage = Thread(target=visitorImage_thread, args=(
            visitID,self.filepath))  # thread created so image is downloaded in the background, and so does not delay loading of screen
            thread_visitorImage.setDaemon(True)
            thread_visitorImage.start()
            data_visitID = {"visitID": visitID}
            response = requests.post(serverBaseURL + "/view_visitorLog", data_visitID).json()
            faceID = response[1]
            confidence = response[2]
            if confidence != "NO_FACE":  # confidence is set to 'NO_FACE' when a face cannot be detected in the image taken by the doorbell
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
        self.dialog.dismiss()
        if self.ids.faceName.text == 'Face unknown':
            self.updateFaces_dialog()
        self.manager.current = "Homepage"

    def updateFaces_dialog(self):
        # markup used to increase accessibility and usability
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
        global faceID
        self.dialog.dismiss()
        for object in self.dialog.content_cls.children:  # iterates through the objects of the dialog box where the user inputted the name of the visitor
            if isinstance(object, MDTextField):
                faceName = object.text
        data_knownFaces = {"faceName": faceName, "faceID": faceID}
        requests.post(serverBaseURL + "/update_knownFaces", data_knownFaces)
        self.ids.faceName.text = faceName


class DialogContent(BoxLayout):
    pass


class MyApp(MDApp):
    # 'MyApp' class is used to create app GUI by building 'layout.kv' file
    def build(self, **kw):
        layout = Builder.load_file("layout.kv")  # loads the 'layout.kv' file
        return layout

def visitorImage_thread(visitID, filepath):
    downloadData = {"bucketName": "nea-visitor-log",
                    "s3File": visitID}  # creates the dictionary which stores the metadata required to download the pkl file of the image from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
    response_text = "error"
    while response_text == "error":
        response = requests.post(serverBaseURL + "/downloadS3", downloadData)
        response_text = response.text
        time.sleep(0.5)
    visitorImage_data = response.content
    path_visitorImage = join(filepath, 'visitorImage.png')
    f = open(path_visitorImage, 'wb')
    f.write(visitorImage_data)
    f.close()
    visitorImage = AsyncImage(source=path_visitorImage,
                              # AsyncImage used as it runs as a background thread, so if the image cannot be loaded, this won't hold up program
                              pos_hint={"center_x": 0.5,
                                        "center_y": 0.53})  # AsyncImage loads image as background thread
    visitorImage.reload()  # reloads the image file to ensure the latest stored image is used
    MDApp.get_running_app().manager.get_screen('VisitorImage').ids.visitorImage.add_widget(
        visitorImage)  # accesses screen ids and adds the visitor image as a widget to a nested float layout
    MDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 0


def createThread_ring(accountID, filepath):
    MQTT = autoclass('MQTT')
    mqtt = MQTT.alloc().init()
    mqtt.ringTopic = f"ring/{accountID}"
    mqtt.visitTopic = f"visit/{accountID}"
    mqtt.connect()  # connect to to mqtt broker
    # mqtt must be instantiated outside of thread otherwise connection is unnsuccessful
    thread_ring = Thread(target=ringThread, args=(mqtt,filepath))
    thread_ring.setDaemon(True)
    thread_ring.start()


def createThread_visit(visitID):
    thread_visit = Thread(target=visitThread, args=(visitID,))
    thread_visit.setDaemon(True)
    thread_visit.start()


def ringThread(mqtt, filepath):
    while True:
        if mqtt.messageReceived_ring == 1:
            mqtt.messageReceived_ring = 0  # value of 'messageReceived' must be set to 0 so that new messages can be received
            mqtt.vibratePhone()
            MDApp.get_running_app().manager.current = "RingAlert"
            visitID = str(mqtt.messageData.UTF8String())
            downloadData = {"bucketName": "nea-visitor-log",
                            "s3File": visitID}  # creates the dictionary which stores the metadata required to download the pkl file of the image from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
            time.sleep(2)
            response_text = "error"
            while response_text == "error":
                response = requests.post(serverBaseURL + "/downloadS3", downloadData)
                response_text = response.text
                time.sleep(0.5)
            createThread_visit(visitID)  # visit thread only called once doorbell is rung to save battery life
            visitorImage_data = response.content
            f = open(join(filepath, 'visitorImage.png'), 'wb')
            f.write(visitorImage_data)
            f.close()
            time.sleep(0.2)  # delay to save image
            MDApp.get_running_app().manager.current = "VisitorImage"
            visitorImage = AsyncImage(source=join(filepath, 'visitorImage.png'),
                                      pos_hint={"center_x": 0.5,
                                                "center_y": 0.53})  # AsyncImage loads image as background thread
            visitorImage.reload()  # reloads the image file to ensure the latest stored image is used
            mqtt.notifyPhone()
            MDApp.get_running_app().manager.get_screen('VisitorImage').ids.visitorImage.add_widget(
                visitorImage)  # accesses screen ids and adds the visitor image as a widget to a nested float layout
            MDApp.get_running_app().manager.get_screen('VisitorImage').ids.loading.opacity = 0
            MDApp.get_running_app().manager.get_screen('VisitorImage').ids.faceName.text = "Loading..."
        else:
            time.sleep(3)  # save battery as looping less often


def visitThread(visitID):
    global faceID
    while True:
        data_visitID = {"visitID": visitID}
        response = None
        while response == None:  # loop until visitID record has been added to db by Raspberry Pi (ensures no error arises in case of latency between RPi inserting vistID data to db and mobile app retrieving this data here)
            response = requests.post(serverBaseURL + "/view_visitorLog", data_visitID).json()
            time.sleep(1)
        faceID = response[1]
        confidence = response[2]
        if confidence != "NO_FACE":  # confidence is set to 'NO_FACE' when a face cannot be detected in the image taken by the doorbell
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
    start_time = time.time()
    dbData_id = {'id': id}
    while True:
        response = (requests.post(serverBaseURL + "/verifyPairing", dbData_id).json())[
            'result']  # sends post request to 'verifyAccount' route on AWS server to check whether the email address inputted is already associated with an account
        print(response)
        if response == accountID and pairing == True:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = f"Successfully paired with SmartBell '{id}'!\n"
            MDApp.get_running_app().manager.get_screen('Homepage').snackbar()
            loggedIn = jsonStore.get("localData")["loggedIn"]
            accountID = jsonStore.get("localData")["accountID"]
            jsonStore.put("localData", initialUse=False, loggedIn=loggedIn, accountID=accountID, paired=id)
            break
        elif response == '' and pairing == False:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = f"Successfully unpaired from SmartBell '{id}'\n"
            MDApp.get_running_app().manager.get_screen('Homepage').snackbar()
            break
        elif response != accountID and response != None and response != '' and pairing == True:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = 'Error pairing SmartBell. Please ensure you\ninput the correct name for your SmartBell\n'
            MDApp.get_running_app().manager.get_screen('Homepage').snackbar()
            break
        elif time.time() - start_time > 60:
            MDApp.get_running_app().manager.get_screen(
                'Homepage').ids.snackbar.text = 'Error pairing SmartBell. Please ensure you\ninput the correct name for your SmartBell\n'
            MDApp.get_running_app().manager.get_screen('Homepage').snackbar()
            break
        time.sleep(1)


if __name__ == "__main__":  # when the program is launched, if the name of the file is the main program (i.e. it is not a module being imported by another file) then this selection statement is True
    MyApp().run()  # the run method is inherited from the 'MDApp' class which is inherited by the class 'MyApp'



