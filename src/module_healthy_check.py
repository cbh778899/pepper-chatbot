from naoqi import ALProxy, ALModule
import time


class HealthyCheckModule(ALModule):
    def __init__(self, name, webview_url):
        ALModule.__init__(self, name)
        self.BIND_PYTHON( self.getName(),"callback" )

        self.got_pong = False
        self.webview_url = webview_url
        
        self.memory = ALProxy("ALMemory")
        self.tablet_service = ALProxy("ALTabletService")
        self.memory.subscribeToEvent("HealthyCheck", name, "pong")
    
    def ping(self):
        self.memory.raiseEvent("HealthyCheck", "ping")
        self.got_pong = False
        time.sleep(1)
        if not self.got_pong:
            print("Not Got pong")
            self.tablet_service.showWebview(self.webview_url)
            time.sleep(1)

    def pong(self, event_name, value):
        if value == 'pong':
            self.got_pong = True
