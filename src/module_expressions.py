# -*- coding: utf-8 -*-
import json
import random
import re
from naoqi import ALProxy

class BehaviourExecutor:
    def __init__(self, behaviours_file):
        with open(behaviours_file, 'r') as file:
            self.behaviours = json.load(file)

    def sanitize_behaviour_requests(self, chat_response):
        """
        Replace behaviour request keywords with full animation paths
        
        Finds the keywords in braces that are after the 'start', 'wait', 'stop', and 'run' keywords and replaces them with the full path to the animation.
        
        Example:
            "^start(hey) Goodbye ^wait(hey)” will become "^start(animations/Stand/Gestures/Hey_4) Goodbye ^wait(animations/Stand/Gestures/Hey_4)"
        """

        print("Sanitizing chat response: '{}'".format(chat_response))
        
        # Dictionary to store the mapping of keywords to selected behaviours
        keyword_to_behaviour = {}
        behaviour_triggered = False

        # Function to replace keywords with full animation paths
        def replace_keyword(match):
            global behaviour_triggered
            keyword = match.group(2)
            if keyword not in keyword_to_behaviour:
                # Search for the behaviour key in the behaviours
                behaviour = next((b for b in self.behaviours if b['behaviour_key'] == keyword), None)
                if behaviour:
                    selected_behaviour = random.choice(behaviour['behaviour_variations'])
                    keyword_to_behaviour[keyword] = selected_behaviour
                    print("Keyword '{}' mapped to behaviour: {}".format(keyword, selected_behaviour))
                    behaviour_triggered = True
                else:
                    print("No behaviour found for keyword: '{}'".format(keyword))
                    return match.group(0)  # Return the original match if no behaviour is found
            return "^{}({})".format(match.group(1), keyword_to_behaviour[keyword])

        # Replace all occurrences of the keywords in the chat response
        sanitized_response = re.sub(r'\^(start|wait|stop|run)\((.*?)\)', replace_keyword, chat_response)
        
        print("Sanitized chat response: '{}'".format(sanitized_response))
        return sanitized_response, behaviour_triggered

# Example usage:
# executor = BehaviourExecutor('/path/to/behaviours.json')
# sanitized_response, behaviour_triggered = executor.sanitize_behaviour_requests("^start(hey) Goodbye ^wait(hey)")
# print(sanitized_response, behaviour_triggered)
# >> ^start(animations/Stand/Gestures/Hey_4) Goodbye ^wait(animations/Stand/Gestures/Hey_4) True
