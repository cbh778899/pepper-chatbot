from naoqi import ALProxy, ALModule

class EyeContactModule(ALModule):
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.BIND_PYTHON( self.getName(),"callback" )

        self.face_detected = False
        
        self.memory = ALProxy("ALMemory")
        self.memory.subscribeToEvent("FaceDetected", name, "on_face_detected")
    

    def __del__( self ):
        print( "INF: EyeContactModule.__del__: cleaning everything" )
        self.stop()

    def on_face_detected(self, event_name, value):
        if value and not self.face_detected:
            self.handle_status_change(True)
        elif not value and self.face_detected:
            self.handle_status_change(False)

    def handle_status_change(self, status):
        # print(status)
        # if status:
        #     self.speech.say("Hello, I'm pepper, how can I help you today?")
        self.face_detected = status
        self.memory.raiseEvent('EyeContact', status)


    def stop(self):
        self.memory.unsubscribeToEvent("FaceDetected", self.getName())
        print( "INF: EyeContactModule: stopped!" )