from naoqi import ALModule, ALProxy
import time
from tools import chat_completion
from module_expressions import BehaviourExecutor

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

        self.messages = []
        self.system_prompt = system_prompt
        self.reset_message()
        self.behaviour_file = behavior_file

        self.response_finished = True

        self.server_url = server_url
        self.base_route = base_route
        self.api_key = api_key
        self.model_name = model_name

        self.speech = ALProxy('ALAnimatedSpeech')
        self.memory = ALProxy("ALMemory", self.strNaoIp, self.port)
        self.memory.subscribeToEvent("ResetConversation", self.getName(), "reset_message")

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
        # If pepper is triggered, only respond to messages that contain the trigger keywords
        PEPPER_TRIGGER = True
        PEPPER_TRIGGER_KEYWORDS = [
            "pepper", "peper", "peppa", "pepa", "papa", "pappa", "piper", "pipper", 
            "pipa", "pippa", "poppa", "pepor", "pepur", "pepr", "peppar", "peppur", 
            "peppor", "peppur", "pepur", "pepor", "pepr", "peppur", "peppor", "pepur"
        ]

        # the LLM will set conversation_ongoing to True if it believes the conversation is ongoing
        # When the LLM sets to false, we should reset the conversation_ongoing flag
        # New conversation will be triggered by seeing if the keywords are present and setting conversation_ongoing to True
        
        # If we are in a pepper trigger mode, we should only respond to messages that contain the trigger keywords
        if not self.conversation_ongoing and PEPPER_TRIGGER and not any(keyword in message.lower() for keyword in PEPPER_TRIGGER_KEYWORDS):
            print("DEBUG: No Conversation ongoing and my name was not heard.")
            return
        
        print("DEBUG: Received message: {}".format(message))
        
        self.messages.append({'role':'user', 'content': message})
        
        start_time = time.time()

        # Send the message to the chatbot server
        resp_text = chat_completion(
        self.server_url, 
        self.messages, 
        route=self.base_route, 
        model_name=self.model_name, 
        api_key=self.api_key
        )
        
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
                behaviour_request = message_dict.get('behaviour_request', '')
                behaviour_order = message_dict.get('behaviour_order', 'before')
                respond = message_dict.get('respond', False)
                self.conversation_ongoing = message_dict.get('conversation_ongoing', False)
                
                if behaviour_request and not chat_response:
                    print("DEBUG: No text response, but message does not contain 'behaviour_request'.")

                elif not respond or not chat_response:
                    print("DEBUG: Message does not contain 'chat_response' or told not to respond.")
                    return

                # If we want to respond, only respond if we have a chat_response
                elif chat_response:
                    resp_message = chat_response

                elif not behaviour_request:
                        print("DEBUG: No text response, but message does not contain 'behaviour_request'.")
                        return

            except (SyntaxError, NameError) as e:
                print("DEBUG: Failed to decode message: {}".format(e))
                return
            
            behaviour_triggered = False
            
            # Only dispaly the message if the chatbot wants to respond
            self.memory.raiseEvent("Listening", message)

            # Handle behaviour request
            if behaviour_request and behaviour_order == 'before':
                print("DEBUG: Executing behaviour with behaviour_request: {}".format(behaviour_request))
                behaviour_triggered = self.executor.execute_behaviour(behaviour_request, nao_ip=self.strNaoIp, nao_port=self.port)
              
            print("AI Inference Result:\n================================\n"+resp_message+"\n================================\n")
            self.memory.raiseEvent("Speaking", resp_message)
            if respond:
                self.speech.say(resp_message)
            self.memory.raiseEvent("Speaking", None)
            self.messages.append({'role':'assistant','content':resp_message})

            if not behaviour_triggered and behaviour_request and behaviour_order == 'after':
                self.executor.execute_behaviour(behaviour_request, nao_ip=self.strNaoIp, nao_port=self.port)

            if self.save_csv:
                with open('dialogue.csv', 'a') as f:
                    f.write('user,"'+message.replace('"', '\\"')+'"\n')
                    f.write('assistant,"'+resp_message.replace('"', '\\"')+'"\n')
                    if behaviour_request:
                        f.write('behaviour order,"'+behaviour_order.replace('"', '\\"')+'"\n')
                        f.write('behaviour,"'+behaviour_request.replace('"', '\\"')+'"\n')
                    f.close()
