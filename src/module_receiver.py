import re
from naoqi import ALModule, ALProxy
import time
from tools import chat_completion
from module_expressions import BehaviourExecutor
import json

class BaseSpeechReceiverModule(ALModule):
    """
    Use this object to get call back from the ALMemory of the naoqi world.
    Your callback needs to be a method with two parameter (variable name, value).
    """

    def __init__( 
            self, strModuleName, strNaoIp, port, 
            server_url, base_route, api_key, 
            model_name, save_csv=False, system_prompt='', behavior_file='behaviours_described.json'
        ):
        
        ALModule.__init__(self, strModuleName )
        self.BIND_PYTHON( self.getName(),"callback" )

        self.port = port
        self.strNaoIp = strNaoIp

        self.behaviour_file = behavior_file

        self.response_finished = True

        self.server_url = server_url
        self.base_route = base_route
        self.api_key = api_key
        self.model_name = model_name

        self.speech = ALProxy('ALAnimatedSpeech')
        self.memory = ALProxy("ALMemory", self.strNaoIp, self.port)
        self.memory.subscribeToEvent("ResetConversation", self.getName(), "reset_message")

        self.messages = []
        self.system_prompt = system_prompt
        self.reset_message()

        self.save_csv = save_csv
        
        self.conversation_ongoing = False

        if self.save_csv:
            with open('dialogue.csv', 'w') as f:
                f.write('role,content\n')
                f.close()

        print("DEBUG: Initializing BehaviourExecutor with behaviour_file: {}".format(self.behaviour_file))
        self.executor = BehaviourExecutor(self.behaviour_file)

    # __init__ - end
    def __del__( self ):
        print( "INF: ReceiverModule.__del__: cleaning everything" )
        self.stop()

    def sync_messages(self):
        msg = self.messages
        if self.system_prompt: msg = [i for i in self.messages if i['role'] != 'system']
        self.memory.raiseEvent("SyncMessages", json.dumps(msg))

    def reset_message(self):
        self.messages = [{
            "role":"system",
            "content": self.system_prompt or "You are an assistant names Pepper, your job is to answer users' questions in short."
        }]
        self.sync_messages()

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
        # If pepper is triggered, only respond to messages that contain the trigger keywords
        PEPPER_TRIGGER = True
        PEPPER_NAME = "Pepper"
        PEPPER_TRIGGER_KEYWORDS = [
            "pepper", "peper", "peppa", "pepa", "papa", "pappa", "piper", "pipper", 
            "pipa", "pippa", "poppa", "pepor", "pepur", "pepr", "peppar", "peppur", 
            "peppor", "peppur", "pepur", "pepor", "pepr", "peppur", "peppor", "pepur"
        ]

        # the LLM will set conversation_ongoing to True if it believes the conversation is ongoing
        # When the LLM sets to false, we should reset the conversation_ongoing flag
        # New conversation will be triggered by seeing if the keywords are present and setting conversation_ongoing to True
        print("DEBUG: Received message: {}".format(message))
        
        # Replace all trigger keywords with "Pepper" in the message        
        for keyword in PEPPER_TRIGGER_KEYWORDS:
            message = re.sub(r'\b{}\b'.format(re.escape(keyword)), PEPPER_NAME, message, flags=re.IGNORECASE)

        # If we are in a pepper trigger mode, we should only respond to messages that contain "Pepper"
        if not self.conversation_ongoing and PEPPER_TRIGGER:
            if PEPPER_NAME.lower() not in message.lower():
                print("DEBUG: Message does not contain the trigger keyword 'Pepper'.")
                return

        print("DEBUG: Sanitised message: {}".format(message))
        
        self.messages.append({'role':'user', 'content': message})
        self.sync_messages()
        
        start_time = time.time()

        self.memory.raiseEvent("Speaking", "[LOGS][THINK_RESP]I heard you said \""+message+"\", let me think...")
        # Send the message to the chatbot server
        resp_text = chat_completion(
        self.server_url, 
        self.messages, 
        route=self.base_route, 
        model_name=self.model_name, 
        api_key=self.api_key
        )
        self.memory.raiseEvent("Speaking", None)
        
        print("DEBUG: Received response text: {}".format(resp_text))
        print("DEBUG: Response took {} seconds.".format(time.time() - start_time))
        
        # Sanitize the response text to extract only the JSON component
        json_start = resp_text.find('{')
        json_end = resp_text.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            resp_text = resp_text[json_start:json_end]
        else:
            print("DEBUG: No valid JSON found in response text.")
            return
        
        if resp_text:
            # Decode the message JSON format, example: {'chat_response': 'Hey, how are you?', 'behaviour_request': 'hey', 'behaviour_order': 'before'}
            # Only decode the message if it is in the correct JSON format
            try:
                message_dict = eval(resp_text.replace('true', 'True').replace('false', 'False'))
                chat_response = message_dict.get('chat_response', '')
                self.conversation_ongoing = message_dict.get('conversation_ongoing', False)
                
                if not chat_response:
                    print("DEBUG: Message does not contain 'chat_response' or told not to respond.")
                    return

                # If we want to respond, only respond if we have a chat_response
                elif chat_response:
                    # Sanitize the chat_response to replace behaviour requests with full paths
                    chat_response, behaviour_triggered = self.executor.sanitize_behaviour_requests(chat_response)
                    resp_message = chat_response
                
                else:
                    print("DEBUG: Message does not contain 'chat_response'.")
                    return

            except (SyntaxError, NameError) as e:
                print("DEBUG: Failed to decode message: {}".format(e))
                return
            
            behaviour_triggered = False
            
            # Only dispaly the message if the chatbot wants to respond
            self.memory.raiseEvent("Listening", message)
 
            print("AI Inference Result:\n================================\n"+resp_message+"\n================================\n")
            self.memory.raiseEvent("Speaking", resp_message)
            self.speech.say(resp_message)
            self.memory.raiseEvent("Speaking", None)
            self.messages.append({'role':'assistant','content':resp_message})

            if self.save_csv:
                with open('dialogue.csv', 'a') as f:
                    f.write('user,"'+message.replace('"', '\\"')+'"\n')
                    f.write('assistant,"'+resp_message.replace('"', '\\"')+'"\n')
                    if behaviour_triggered:
                        f.write('behaviour triggered,"'+behaviour_triggered.replace('"', '\\"')+'"\n')
                    f.close()
