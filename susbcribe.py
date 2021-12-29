import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set(username="yrczhohs", password="qPSwbxPDQHEI")
client.connect("hairdresser.cloudmqtt.com", 18973)

def on_message(i,h, msg):
    print(msg.payload.decode())

client.subscribe("testing")
client.message_callback_add("testing", on_message)

client.loop_forever()