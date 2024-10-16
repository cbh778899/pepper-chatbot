import json
import random
from naoqi import ALProxy

class BehaviourExecutor:
    def __init__(self, behaviours_file):
        with open(behaviours_file, 'r') as file:
            self.behaviours = json.load(file)

    def execute_behaviour(self, behaviour_key, nao_ip="10.234.7.154", nao_port=9559):
        print("Executing behaviour with key: '{}', nao_ip: {}, nao_port: {}".format(behaviour_key, nao_ip, nao_port))
        behaviour_triggered = False
        self.memory = ALProxy("ALMemory", nao_ip, nao_port)

        # Search for the behaviour key in the behaviours
        behaviour = next((b for b in self.behaviours if b['behaviour_key'] == behaviour_key), None)
        
        if behaviour:
            print("Behaviour key matched: '{}'".format(behaviour_key))
            selected_behaviour = random.choice(behaviour['behaviour_variations'])
            print("Selected behaviour: {}".format(selected_behaviour))
            
            # Convert selected_behaviour to string if it is not
            if not isinstance(selected_behaviour, str):
                selected_behaviour = str(selected_behaviour)

            # Log the selected behaviour path
            print("Selected behaviour path: {}".format(selected_behaviour))

            animation_player_service = ALProxy("ALAnimationPlayer", nao_ip, nao_port)
            print("Running behaviour: {}".format(selected_behaviour))
            try:
                self.memory.raiseEvent("Speaking", selected_behaviour)
                animation_player_service.run(selected_behaviour, _async=False)
                self.memory.raiseEvent("Speaking", None)
            except RuntimeError as e:
                print("Error running behaviour: {}".format(e))
                return False

            behaviour_triggered = True

        print("Behaviour triggered: {}".format(behaviour_triggered))
        return behaviour_triggered

# Example usage:
# executor = BehaviourExecutor('/path/to/behaviours.json')
# behaviour_triggered = executor.execute_behaviour("countfour", nao_ip="10.234.7.154", nao_port=9559)
