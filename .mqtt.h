/** MQTTClient header file must be imported to access associated protocols required to implement MQTT
 */
#import "MQTTClient.h"


/** 'MQTT' is name of custom class which conforms to protocol 'MQTTSessionDelegate' (a protocol is used to declare methods and properties which are independent of a class). Therefore, the 'MQTT' class implements the methods associated with the 'MQTTSessionDelegate' protocol.
 */
@interface MQTT: NSObject <MQTTSessionDelegate>


/** The following properties are properties of the 'MQTT' class
 */
@property (nonatomic) int messageReceived_ring;
@property (nonatomic, assign) NSString *messageData;
@property (nonatomic, assign) NSString *ringTopic;
@property (nonatomic, assign) NSString *publishData;
@property (nonatomic, assign) NSString *publishTopic;

@end




