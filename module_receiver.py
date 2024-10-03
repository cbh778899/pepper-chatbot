# -*- coding: utf-8 -*-

###########################################################
# This module receives results from the speechrecognition module and prints to console
#
# Syntax:
#    python scriptname --pip <ip> --pport <port>
#
#    --pip <ip>: specify the ip of your robot (without specification it will use the NAO_IP defined below
#
# Author: Johannes Bramauer, Vienna University of Technology
# Created: May 30, 2018
# License: MIT
###########################################################

# NAO_PORT = 65445 # Virtual Machine

import naoqi
from naoqi import ALProxy
import urllib2
import json

class BaseSpeechReceiverModule(naoqi.ALModule):
    """
    Use this object to get call back from the ALMemory of the naoqi world.
    Your callback needs to be a method with two parameter (variable name, value).
    """

    def __init__( self, strModuleName, strNaoIp, port, server_base_route, auth_key = 'no-key' ):
        self.messages = [{"role":"system","content":"You are an assistant names Pepper, your job is to answer users' questions. The questions are converted from audio so it sometimes unclear, please consider this and answer questions."}]
        self.server_base_route = server_base_route
        self.response_finished = True
        self.port = port
        self.auth_key = auth_key
        self.strNaoIp = strNaoIp
        self.speech = ALProxy('ALTextToSpeech', strNaoIp, self.port)
        self.memory = naoqi.ALProxy("ALMemory", self.strNaoIp, self.port)

        try:
            naoqi.ALModule.__init__(self, strModuleName )
            self.BIND_PYTHON( self.getName(),"callback" )
        except BaseException as err:
            print( "ERR: ReceiverModule: loading error: %s" % str(err) )

    # __init__ - end
    def __del__( self ):
        print( "INF: ReceiverModule.__del__: cleaning everything" )
        self.stop()

    def start( self ):
        self.memory.subscribeToEvent("SpeechRecognition", self.getName(), "processRemote")
        print( "INF: ReceiverModule: started!" )


    def stop( self ):
        print( "INF: ReceiverModule: stopping..." )
        self.memory.unsubscribe(self.getName())
#	self.speech.stopAll()

        print( "INF: ReceiverModule: stopped!" )

    def version( self ):
        return "1.1"

    def processRemote(self, signalName, message):
        # Do something with the received speech recognition result

        if not self.response_finished: return
        self.response_finished = False

        self.messages.append({'role':'user', 'content': message})

        data = json.dumps({
            'messages': self.messages,
            'max_tokens': 60
        })
        req = urllib2.Request('{}/chat/completions'.format(self.server_base_route), data=data)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', 'Bearer {}'.format(self.auth_key or 'no-key'))

        try:
            # Send the request and get the response
            response = urllib2.urlopen(req)
            
            # Read and parse the response
            response_data = response.read()
            parsed_response = json.loads(response_data)
            
            # Print the parsed response
            resp_text = str(parsed_response['choices'][0]['message']['content'])
            print("AI Inference Result:\n================================\n"+resp_text+"\n================================\n")
            self.memory.raiseEvent("Speaking", True)
            self.speech.say(resp_text)
            self.memory.raiseEvent("Speaking", False)
            self.messages.append({'role':'assistant','content':resp_text})	    

        except urllib2.HTTPError as e:
            print("HTTP Error:", e.code, e.read())

        except urllib2.URLError as e:
            print("URL Error:", e.reason)
        self.response_finished = True

# def main():
#     """ Main entry point

#     """
#     parser = OptionParser()
#     parser.add_option("--pip",
#         help="Parent broker port. The IP address or your robot",
#         dest="pip")
#     parser.add_option("--pport",
#         help="Parent broker port. The port NAOqi is listening to",
#         dest="pport",
#         type="int")
#     parser.add_option("--base-route",
#         help="Base route of OpenAI Server",
#         dest="server_base_route")
#     parser.set_defaults(
#         pip=NAO_IP,
#         pport=NAO_PORT)

#     (opts, args_) = parser.parse_args()
#     pip   = opts.pip
#     pport = opts.pport
#     server_base_route = opts.server_base_route

#     # We need this broker to be able to construct
#     # NAOqi modules and subscribe to other modules
#     # The broker must stay alive until the program exists
#     myBroker = naoqi.ALBroker("myBroker",
#        "0.0.0.0",   # listen to anyone
#        0,           # find a free port and use it
#        pip,         # parent broker IP
#        pport)       # parent broker port

#     try:
#         p = ALProxy("BaseSpeechReceiverModule")
#         p.exit()  # kill previous instance
#     except:
#         pass
#     # Reinstantiate module

#     # Warning: ReceiverModule must be a global variable
#     # The name given to the constructor must be the name of the
#     # variable
#     global BaseSpeechReceiverModule
#     BaseSpeechReceiverModule = BaseSpeechReceiverModule("BaseSpeechReceiverModule", pip, server_base_route)
#     BaseSpeechReceiverModule.start()

#     if(False):
#         #one-shot recording for at least 5 seconds
#         SpeechRecognition = ALProxy("SpeechRecognition")
#         SpeechRecognition.start()
#         SpeechRecognition.setHoldTime(5)
#         SpeechRecognition.setIdleReleaseTime(1.7)
#         SpeechRecognition.setMaxRecordingDuration(10)
#         SpeechRecognition.startRecording()

#     else:
#         # auto-detection
#         SpeechRecognition = ALProxy("SpeechRecognition")
#         SpeechRecognition.start()
#         SpeechRecognition.setHoldTime(2.5)
#         SpeechRecognition.setIdleReleaseTime(1.0)
#         SpeechRecognition.setMaxRecordingDuration(10)
#         SpeechRecognition.setLookaheadDuration(0.5)
#         #SpeechRecognition.setLanguage("de-de")
#         #SpeechRecognition.calibrate()
#         SpeechRecognition.setAutoDetectionThreshold(5)
#         SpeechRecognition.enableAutoDetection()
#         #SpeechRecognition.startRecording()

#     try:
#         while True:
#             time.sleep(1)

#     except KeyboardInterrupt:
#         print
#         print("Interrupted by user, shutting down")
#         myBroker.shutdown()
#         sys.exit(0)



# if __name__ == "__main__":
#     main()