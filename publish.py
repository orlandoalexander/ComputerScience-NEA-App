import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):
    if rc == 0: # if connection is successful
        print("connected")
        client.publish("ring/MzVmXPjQXsIBouwmHM2ISwsJx0SB4UTncAVjnvnKcmI=", "8gPxl74fDKsjdQIWmJf0GeUhb60YqrrvTDrEMZo7JJZ=", retain=True, qos=0)
        client.publish("visit/MzVmXPjQXsIBouwmHM2ISwsJx0SB4UTncAVjnvnKcmI=",
                       "8gPxl74fDKsjdQIWmJf0GeUhb60YqrrvTDrEMZo7JJZ=", retain=True, qos=0)
    else:
        # attempts to reconnect
        print("failed")

client = mqtt.Client()
client.username_pw_set(username="yrczhohs", password="qPSwbxPDQHEI")
client.on_connect = on_connect

client.connect("hairdresser.cloudmqtt.com", 18973)
client.loop_forever()

# serverBaseURL = "http://nea-env.eba-6tgviyyc.eu-west-2.elasticbeanstalk.com/"
# import wave
# import pickle
# import requests
#
# downloadData = {"bucketName": "nea-audio-messages",
#                                      "s3File": "GD1j9cF9EGYVpw18"}  # creates the dictionary which stores the metadata required to download the pkl file of the personalised audio message from AWS S3 using the 'boto3' module on the AWS elastic beanstalk environment
# response = requests.post(serverBaseURL + "/downloadS3", downloadData)
# audioData = response.content
# audioData = pickle.loads(response.content)  # unpickles the byte string
#
# messageFile = wave.open("test.wav", "wb")
# messageFile.setnchannels(1)  # change to 1 for audio stream module
# messageFile.setsampwidth(2)
# messageFile.setframerate(8000)  # change to 8000 for audio stream module
# messageFile.writeframes(b''.join(audioData))
# messageFile.close()

