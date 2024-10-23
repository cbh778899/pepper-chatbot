from naoqi import ALProxy, ALModule
import time
import json


class HealthyCheckModule(ALModule):
    def __init__(self, name, webview_url):
        ALModule.__init__(self, name)
        self.BIND_PYTHON( self.getName(),"callback" )

        self.got_pong = False
        self.webview_url = webview_url
        
        self.memory = ALProxy("ALMemory")
        self.tablet_service = ALProxy("ALTabletService")
        self.memory.subscribeToEvent("HealthyCheck", name, "pong")
        self.memory.subscribeToEvent("ControlRecording", name, "update_recording")
        self.memory.subscribeToEvent("Speaking", name, "update_speaking")
        self.memory.subscribeToEvent("SyncMessages", name, "update_chat_history")

        self.is_allowed_recording = False
        self.is_speaking = None
        self.chat_history = ''
    
    def ping(self):
        self.memory.raiseEvent("HealthyCheck", "ping")
        self.got_pong = False
        time.sleep(1)
        if not self.got_pong:
            print("Not Got pong")
            self.tablet_service.showWebview(self.webview_url)
            time.sleep(2)
            self.sync()

    def pong(self, event_name, value):
        if value == 'pong':
            self.got_pong = True

    def sync(self):
        self.memory.raiseEvent("Sync", json.dumps({
            "speaking": self.is_speaking,
            "allowed_recording": self.is_allowed_recording,
            "history": self.chat_history
        }))

    def update_recording(self, event_name, value):
        self.is_allowed_recording = value

    def update_speaking(self, event_name, value):
        self.is_speaking = value

    def update_chat_history(self, event_name, value):
        self.chat_history = value
