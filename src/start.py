from module_receiver import BaseSpeechReceiverModule
from module_speechrecognition import SpeechRecognitionModule
from module_eyecontact import EyeContactModule
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
SPEECH_RECOGNITION_ROUTE = os.getenv('SPEECH_RECOGINITION_ROUTE') or '/speech/recognition'

# openai
MODEL_NAME = os.getenv('MODEL_NAME')
API_KEY = os.getenv('API_KEY')
SPEECH_API_KEY = os.getenv('SPEECH_API_KEY') or API_KEY

WEBVIEW = os.getenv('WEBVIEW') or ''

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
    parser.add_option("--chat-route",
        help="Route of chat completion service, default '/chat/completions'",
        dest="chat_route")
    parser.add_option("--speech-route",
        help="Route of speech recognition service, default '/speech/recognition'",
        dest="speech_route")
    parser.add_option("--api-key",
        help="API Key of services",
        dest="api_key")
    parser.add_option("--speech-api-key",
        help="API Key of Speech Service, default to the same of --api-key option",
        dest="speech_api_key")
    parser.add_option("--model-name",
        help="Model name when calling OpenAI API",
        dest="model_name")
    parser.add_option("--save-csv",
        help="Set to enable save conversation to a file called dialogue.csv",
        dest="save_csv",
        action='store_true')
    parser.add_option("--prompt",
        help="Add a system prompt",
        dest="prompt")
    parser.add_option("--fprompt",
        help="Add a system prompt load from a file, specify the file name to . If --prompt is specified, ignore this",
        dest="fprompt")
    parser.add_option("--fbehaviours",
        help="Add a system behaviour json file, specify the file name.",
        dest="fbehaviours")
    parser.add_option("--webview",
        help="Start a webview server when this script starts. Speficy the url of webview.",
        dest="webview")
    parser.set_defaults(
        ip=NAO_IP,
        port=NAO_PORT,
        server_url=URL,
        chat_route=CHAT_COMPLETION_ROUTE,
        speech_route=SPEECH_RECOGNITION_ROUTE,
        api_key=API_KEY,
        speech_api_key=SPEECH_API_KEY,
        model_name=MODEL_NAME,
        save_csv=False,
        prompt='',
        fprompt='',
        fbehaviours='/pepperchat/behaviours/behaviours_described.json',
        webview=WEBVIEW
    )

    opts = parser.parse_args()[0]

    ip   = opts.ip
    port = toint(opts.port)
    server_url = opts.server_url
    chat_route = opts.chat_route
    speech_route = opts.speech_route
    api_key = opts.api_key
    speech_api_key = opts.speech_api_key
    model_name = opts.model_name
    save_csv = opts.save_csv
    prompt=opts.prompt
    fprompt=opts.fprompt
    fbehaviours=opts.fbehaviours
    webview = opts.webview

    if not server_url:
        print('Error: Services route not specified!')
        return
    
    try:
        if not prompt and fprompt:
            prompt_file = open(fprompt, 'r')
            prompt = prompt_file.read().strip()
            prompt_file.close()
    except:
        print('\n\nLoading prompt failed, does the file exists? Using the default, blank prompt...\n\n')
        prompt = ''

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
    memory.declareEvent("Listening")
    memory.declareEvent("EyeContact")
    memory.declareEvent("ResetConversation")
    
    # turn off native pepper speech recognition
    asr = ALProxy("ALSpeechRecognition", ip, port)
    asr.setVisualExpression(False)  # disable LEDs for when speech is detected (spinning blue eyes)
    asr.setAudioExpression(False)   # disable beep noise when speech is detected

    speech_recoginition_url = os.getenv('SPEECH_RECOGINITION_URL') or server_url

    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule(
        "SpeechRecognition", ip, port,
        speech_recoginition_url, speech_route, speech_api_key
    )

    global EyeContact
    EyeContact = EyeContactModule("EyeContact")

    # auto-detection
    SpeechRecognition.setHoldTime(tofloat(os.getenv('HOLD_TIME')) or 2.0)
    SpeechRecognition.setIdleReleaseTime(tofloat(os.getenv('RELEASE_TIME')) or 1.0)
    SpeechRecognition.setMaxRecordingDuration(tofloat(os.getenv('RECORD_DURATION')) or 7.0)
    SpeechRecognition.setLookaheadDuration(tofloat(os.getenv('LOOK_AHEAD_DURATION')) or 0.5)
    SpeechRecognition.setAutoDetectionThreshold(toint(os.getenv('AUTO_DETECTION_THREADSHOLD')) or 5)
    SpeechRecognition.enableAutoDetection()
    SpeechRecognition.start()

    global Receiver
    Receiver = BaseSpeechReceiverModule(
        "Receiver", ip, port,
        server_url=server_url, base_route=chat_route,
        api_key=api_key, model_name=model_name, save_csv=save_csv,
        system_prompt=prompt, behavior_file=fbehaviours
    )
    Receiver.start()

    if webview:
        tablet_service = ALProxy("ALTabletService")
        tablet_service.loadUrl(webview)
        tablet_service.showWebview()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("Interrupted by user, shutting down")
        myBroker.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()