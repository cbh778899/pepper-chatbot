from module_receiver import BaseSpeechReceiverModule
from module_speechrecognition import SpeechRecognitionModule
from naoqi import ALProxy, ALBroker

import time
import os
import sys

from optparse import OptionParser
from tools import load_env, toint, tofloat

load_env()

NAO_IP = os.getenv('NAO_IP') or "localhost"
NAO_PORT = toint(os.getenv('NAO_PORT')) or 9559

# server
URL = os.getenv('URL')
CHAT_COMPLETION_ROUTE = os.getenv('CHAT_COMPLETION_ROUTE') or "/chat/completions"

# openai
MODEL_NAME = os.getenv('MODEL_NAME')
API_KEY = os.getenv('API_KEY')

def main():
    parser = OptionParser()
    parser.add_option("--ip",
        help="Parent broker port. The IP address or your robot",
        dest="ip")
    parser.add_option("--port",
        help="Parent broker port. The port NAOqi is listening to",
        dest="port",
        type="int")
    parser.add_option("--url",
        help="Base url of OpenAI-llike Server",
        dest="server_url")
    parser.add_option("--route",
        help="Route of chat completion server, default '/chat/completions'",
        dest="route")
    parser.add_option("--api-key",
        help="API Key of OpenAI APIs",
        dest="api_key")
    parser.add_option("--model-name",
        help="Model name when calling OpenAI API",
        dest="model_name")
    parser.add_option("--save-csv",
        help="Set to enable save conversation to a file called dialogue.csv",
        dest="save_csv",
        action='store_true')
    parser.set_defaults(
        ip=NAO_IP,
        port=NAO_PORT,
        server_url=URL,
        route=CHAT_COMPLETION_ROUTE,
        api_key=API_KEY,
        model_name=MODEL_NAME,
        save_csv=False
    )

    opts = parser.parse_args()[0]

    ip   = opts.ip
    port = toint(opts.port)
    server_url = opts.server_url
    route = opts.route
    api_key = opts.api_key
    model_name = opts.model_name
    save_csv = opts.save_csv

    # setup broker to use memory and different modules
    myBroker = ALBroker("myBroker",
       "0.0.0.0", # listen to anyone
       0,         # find a free port and use it
       ip,        # parent broker IP
       port       # parent broker port
    )

    try:
        p = ALProxy("SpeechRecognition")
        p.exit()  # kill previous instance, useful for developing ;)
    except:
        pass

    # declear events sharing between different modules
    memory = ALProxy("ALMemory")
    memory.declareEvent("SpeechRecognition")
    memory.declareEvent("Speaking")

    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", ip, port)

    # auto-detection
    SpeechRecognition.start()
    SpeechRecognition.setHoldTime(tofloat(os.getenv('HOLD_TIME')) or 2.0)
    SpeechRecognition.setIdleReleaseTime(tofloat(os.getenv('RELEASE_TIME')) or 1.0)
    SpeechRecognition.setMaxRecordingDuration(tofloat(os.getenv('RECORD_DURATION')) or 7.0)
    SpeechRecognition.setLookaheadDuration(tofloat(os.getenv('LOOK_AHEAD_DURATION')) or 0.5)
    SpeechRecognition.setAutoDetectionThreshold(toint(os.getenv('AUTO_DETECTION_THREADSHOLD')) or 5)
    SpeechRecognition.enableAutoDetection()

    global BaseSpeechReceiver
    BaseSpeechReceiver = BaseSpeechReceiverModule(
        "BaseSpeechReceiver", ip, port,
        server_url=server_url, base_route=route,
        api_key=api_key, model_name=model_name, save_csv=save_csv
    )
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
