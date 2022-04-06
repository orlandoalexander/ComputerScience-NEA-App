#import "mqtt.h"
#import <AudioToolbox/AudioToolbox.h>

/** defines the methods for the 'MQTT' class
 */
@implementation MQTT
- (id) init {
    
    return self;
}

- (void) connect {
    
        MQTTCFSocketTransport*transport = [[MQTTCFSocketTransport alloc] init];
        transport.host = @"hairdresser.cloudmqtt.com";
        transport.port = 18973;
    
        MQTTSession *session = [[MQTTSession alloc] init];
        session.delegate = self;
        session.transport = transport;
        session.userName = @"yrczhohs";
        session.password = @"qPSwbxPDQHEI";
        session.protocolLevel = MQTTProtocolVersion31;
        self.messageReceived_ring = 0;
    
        [session connectAndWaitTimeout:30];

        [session subscribeToTopic:self.ringTopic atLevel:2];
}
    
- (void)newMessage:(MQTTSession *)session data:(NSData *)data onTopic:(NSString *)topic qos:(MQTTQosLevel)qos retained:(BOOL)retained mid:(unsigned int)mid {
        
        NSString* dataStr = [[NSString alloc] initWithData:data
                                             encoding:NSUTF8StringEncoding];
 
    if (![dataStr isEqualToString:@""] && [topic isEqualToString:self.ringTopic] ){
            self.messageData = dataStr;
            self.messageReceived_ring = 1;
    }
}
    
- (void) publish {
    
    MQTTCFSocketTransport*transport = [[MQTTCFSocketTransport alloc] init];
    transport.host = @"hairdresser.cloudmqtt.com";
    transport.port = 18973;

    MQTTSession *session = [[MQTTSession alloc] init];
    session.transport = transport;
    session.userName = @"yrczhohs";
    session.password = @"qPSwbxPDQHEI";
    session.protocolLevel = MQTTProtocolVersion31;
    [session setDelegate:self];
    [session connectAndWaitTimeout:30];

    NSData* data = [self.publishData dataUsingEncoding:NSUTF8StringEncoding];
    [session publishData:data
                        onTopic:self.publishTopic
                         retain:NO
                            qos:1];
    [session disconnect ];
}

- (void)vibratePhone; {
    
    AudioServicesPlayAlertSound(4095);
}

- (void)notifyPhone; {
    
     AudioServicesPlayAlertSound(1022);

}

@end


