from module_receiver import BaseSpeechReceiverModule
from module_speechrecognition import SpeechRecognitionModule
from optparse import OptionParser

NAO_IP = "0.0.0.0"
NAO_PORT = 9559

import naoqi
import time
import sys
# from naoqi import ALProxy


def main():
    parser = OptionParser()
    parser.add_option("--pip",
        help="Parent broker port. The IP address or your robot",
        dest="pip")
    parser.add_option("--pport",
        help="Parent broker port. The port NAOqi is listening to",
        dest="pport",
        type="int")
    parser.add_option("--base-route",
        help="Base route of OpenAI Server",
        dest="server_base_route")
    parser.set_defaults(
        pip=NAO_IP,
        pport=NAO_PORT
    )

    (opts, args_) = parser.parse_args()
    pip   = opts.pip
    pport = opts.pport
    server_base_route = opts.server_base_route
    auth_key = opts.auth_key

    myBroker = naoqi.ALBroker("myBroker",
       "0.0.0.0",   # listen to anyone
       0,           # find a free port and use it
       pip,         # parent broker IP
       pport)       # parent broker port

    try:
        p = ALProxy("BaseSpeechReceiverModule")
        p.exit()  # kill previous instance
    except:
        pass

    memory = naoqi.ALProxy("ALMemory")
    memory.declareEvent("SpeechRecognition")
    memory.declareEvent("Speaking")

    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", pip, pport)

    # auto-detection
    # SpeechRecognition = ALProxy("SpeechRecognition")
    SpeechRecognition.start()
    SpeechRecognition.setHoldTime(2.0)
    SpeechRecognition.setIdleReleaseTime(1.0)
    SpeechRecognition.setMaxRecordingDuration(7)
    SpeechRecognition.setLookaheadDuration(0.5)
    #SpeechRecognition.setLanguage("de-de")
    #SpeechRecognition.calibrate()
    SpeechRecognition.setAutoDetectionThreshold(5)
    SpeechRecognition.enableAutoDetection()
    #SpeechRecognition.startRecording()

    global BaseSpeechReceiver
    BaseSpeechReceiver = BaseSpeechReceiverModule("BaseSpeechReceiver", pip, pport, server_base_route, auth_key=auth_key)
    BaseSpeechReceiver.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print
        print("Interrupted by user, shutting down")
        myBroker.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()
