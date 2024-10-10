from naoqi import ALModule, ALProxy
from tools import chat_completion

class BaseSpeechReceiverModule(ALModule):
    """
    Use this object to get call back from the ALMemory of the naoqi world.
    Your callback needs to be a method with two parameter (variable name, value).
    """

    def __init__( 
            self, strModuleName, strNaoIp, port, 
            server_url, base_route, api_key, 
            model_name, save_csv=False, system_prompt='' 
        ):
        
        ALModule.__init__(self, strModuleName )
        self.BIND_PYTHON( self.getName(),"callback" )

        self.port = port
        self.strNaoIp = strNaoIp

        self.messages = []
        self.system_prompt = system_prompt
        self.reset_message()

        self.response_finished = True

        self.server_url = server_url
        self.base_route = base_route
        self.api_key = api_key
        self.model_name = model_name

        self.speech = ALProxy('ALTextToSpeech')
        self.memory = ALProxy("ALMemory", self.strNaoIp, self.port)
        self.memory.subscribeToEvent("ResetConversation", self.getName(), "reset_message")

        self.save_csv = save_csv

        if self.save_csv:
            with open('dialogue.csv', 'w') as f:
                f.write('role,content\n')
                f.close()

    # __init__ - end
    def __del__( self ):
        print( "INF: ReceiverModule.__del__: cleaning everything" )
        self.stop()

    def reset_message(self):
        self.messages = [{
            "role":"system",
            "content": self.system_prompt or "You are an assistant names Pepper, your job is to answer users' questions in short."
        }]

    def start( self ):
        self.memory.subscribeToEvent("SpeechRecognition", self.getName(), "processRemote")
        # print( "INF: ReceiverModule: started!" )


    def stop( self ):
        print( "INF: ReceiverModule: stopping..." )
        try:
            self.memory.unsubscribe('SpeechRecognition', self.getName())
        finally:
            print( "INF: ReceiverModule: stopped!" )

    def version( self ):
        return "1.1"

    def processRemote(self, signalName, message):
        # Do something with the received speech recognition result

        if not self.response_finished: return
        self.response_finished = False

        self.messages.append({'role':'user', 'content': message})
        resp_text = chat_completion(
            self.server_url, 
            self.messages, 
            route=self.base_route, 
            model_name=self.model_name, 
            api_key=self.api_key
        )

        if resp_text:
            print("AI Inference Result:\n================================\n"+resp_text+"\n================================\n")
            self.memory.raiseEvent("Speaking", resp_text)
            self.speech.say(resp_text)
            self.memory.raiseEvent("Speaking", None)
            self.messages.append({'role':'assistant','content':resp_text})

            if self.save_csv:
                with open('dialogue.csv', 'a') as f:
                    f.write('user,"'+message.replace('"', '\\"')+'"\n')
                    f.write('assistant,"'+resp_text.replace('"', '\\"')+'"\n')
                    f.close()

        self.response_finished = True
