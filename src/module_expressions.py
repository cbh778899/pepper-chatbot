import json
import random
from naoqi import ALProxy
import re

class BehaviourExecutor:
    def __init__(self, behaviours_file):
        with open(behaviours_file, 'r') as file:
            self.behaviours = json.load(file)

    def execute_behaviour(self, message, is_input=True, nao_ip="10.234.7.154", nao_port=9559):
        print "Executing behaviour with message: '{}', is_input: {}, nao_ip: {}, nao_port: {}".format(message, is_input, nao_ip, nao_port)
        keywords_type = 'input_keywords' if is_input else 'output_keywords'
        should_respond = True
        behaviour_triggered = False

        for behaviour in self.behaviours:
            messages = re.findall(r'\b\w+\b', message.lower())
            if any(keyword in messages for keyword in behaviour[keywords_type]):
                print "Keyword matched in message: '{}'".format(message)
                selected_behaviour = random.choice(behaviour['behaviours'])
                print "Selected behaviour: {}".format(selected_behaviour)
                
                # Convert selected_behaviour to string if it is not
                if not isinstance(selected_behaviour, str):
                    selected_behaviour = str(selected_behaviour)
                    # print "Error: Selected behaviour is not a string: {}".format(selected_behaviour)
                    # continue

                animation_player_service = ALProxy("ALAnimationPlayer", nao_ip, nao_port)
                chatbot_response = behaviour.get('chatbot_response', False)
                if chatbot_response:
                    print "Running behaviour with following response: {}".format(selected_behaviour)
                    animation_player_service.run(selected_behaviour, _async=False)
                    behaviour_triggered = True
                    return should_respond, behaviour_triggered
                else:
                    print "Running behaviour without response: {}".format(selected_behaviour)
                    animation_player_service.run(selected_behaviour, _async=True)
                    should_respond = False
                    behaviour_triggered = True
                    return should_respond, behaviour_triggered
                break
            # else:
            #     print "No keyword matched in message: '{}'".format(message)

        print "Should respond: {}, Behaviour triggered: {}".format(should_respond, behaviour_triggered)
        return should_respond, behaviour_triggered

# Example usage:
# executor = BehaviourExecutor('/path/to/behaviours.json')
# should_respond, behaviour_triggered = executor.execute_behaviour("some input message", is_input=True, nao_ip=self.strNaoIp, nao_port=self.port)