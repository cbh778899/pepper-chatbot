# -*- coding: utf-8 -*-

###########################################################
# Retrieve robot audio buffer and do google speech recognition
#
# Syntax:
#    python scriptname --pip <ip> --pport <port>
#
#    --pip <ip>: specify the ip of your robot (without specification it will use the NAO_IP defined below)
#
# Author: Johannes Bramauer, Vienna University of Technology
# Created: May 30, 2018
# License: MIT
#
###########################################################
import socket

import numpy as np
import sys
import threading
from naoqi import ALModule, ALProxy
from tools import audio_recoginze, buffer_to_wav_in_memory
from numpy import sqrt, mean, square
import traceback


RECORDING_DURATION = 10      # seconds, maximum recording time, also default value for startRecording(), Google Speech API only accepts up to about 10-15 seconds
LOOKAHEAD_DURATION = 1.0    # seconds, for auto-detect mode: amount of seconds before the threshold trigger that will be included in the request
IDLE_RELEASE_TIME = 2.0     # seconds, for auto-detect mode: idle time (RMS below threshold) after which we stop recording and recognize
HOLD_TIME = 2.0             # seconds, minimum recording time after we started recording (autodetection)
SAMPLE_RATE = 48000         # Hz, be careful changing this, both google and Naoqi have requirements!

CALIBRATION_DURATION = 4    # seconds, timespan during which calibration is performed (summing up RMS values and calculating mean)
CALIBRATION_THRESHOLD_FACTOR = 1.5  # factor the calculated mean RMS gets multiplied by to determine the auto detection threshold (after calibration)

DEFAULT_LANGUAGE = "en-us"  # RFC5646 language tag, e.g. "en-us", "de-de", "fr-fr",... <http://stackoverflow.com/a/14302134>

PREBUFFER_WHEN_STOP = False # Fills pre-buffer with last samples when stopping recording. WARNING: has performance issues!


class SpeechRecognitionModule(ALModule):
    """
    Use this object to get call back from the ALMemory of the naoqi world.
    Your callback needs to be a method with two parameter (variable name, value).
    """

    def __init__( self, strModuleName, strNaoIp, port, stt_url, stt_route='/speech/recognition', stt_api_key='no-key' ):
        try:
            ALModule.__init__(self, strModuleName )

            # is these 2 line necessary? what do they do?
            # just copied them from the examples...
            self.BIND_PYTHON( self.getName(),"callback" )
            self.strNaoIp = strNaoIp

            self.port = port

            self.stt_url = stt_url
            self.stt_route = stt_route
            self.stt_api_key = stt_api_key

            # self.inited = False
            self.isStarted = False

            self.eye_contact = False
            self.is_speaking = False

            self.memory = ALProxy("ALMemory", self.strNaoIp, self.port)
            self.memory.subscribeToEvent("EyeContact", self.getName(), "eye_contact_toggle")
            self.memory.subscribeToEvent("Speaking", self.getName(), "speaking_toggle")

            # flag to indicate if we are currently recording audio
            self.isRecording = False
            self.startRecordingTimestamp = 0
            self.recordingDuration = RECORDING_DURATION

            # flag to indicate if auto speech detection is enabled
            self.isAutoDetectionEnabled = False
            self.autoDetectionThreshold = 10 # TODO: find a default value that works fine so we don't need to calibrate every time

            # RMS calculation variables
            self.framesCount = 0
            self.rmsSum = 0 # used to sum up rms results and calculate average
            self.lastTimeRMSPeak = 0

            # audio buffer
            self.buffer = []
            self.preBuffer = []
            self.preBufferLength = 0    # length in samples (len(self.preBuffer) just counts entries)

            # init parameters
            self.language = DEFAULT_LANGUAGE
            self.idleReleaseTime = IDLE_RELEASE_TIME
            self.holdTime = HOLD_TIME
            self.lookaheadBufferSize = LOOKAHEAD_DURATION * SAMPLE_RATE

            # counter for wav file output
            self.fileCounter = 0

        except BaseException as err:
            print( "ERR: SpeechRecognitionModule: loading error: %s" % str(err) )

    # __init__ - end
    def __del__( self ):
        print( "INF: SpeechRecognitionModule.__del__: cleaning everything" )
        self.stop()

    def start( self ):
        if(self.isStarted):
            return

        # print("INF: SpeechRecognitionModule: starting!")

        self.isStarted = True

        audio = ALProxy( "ALAudioDevice")
        nNbrChannelFlag = 0 # ALL_Channels: 0,  AL::LEFTCHANNEL: 1, AL::RIGHTCHANNEL: 2 AL::FRONTCHANNEL: 3  or AL::REARCHANNEL: 4.
        nDeinterleave = 0
        audio.setClientPreferences( self.getName(),  SAMPLE_RATE, nNbrChannelFlag, nDeinterleave ) # setting same as default generate a bug !?!
        audio.subscribe( self.getName() )

    def pause(self):
        if not self.isStarted:
            return

        self.isStarted = False

        audio = ALProxy("ALAudioDevice")
        audio.unsubscribe(self.getName())

        # print("INF: SpeechRecognitionModule: stopped!")

    def stop( self ):
        self.pause()
        print( "INF: SpeechRecognitionModule: stopped!" )

    def eye_contact_toggle(self, _, has_eye_contact):
        self.eye_contact = has_eye_contact
        self.toggle_status()

    def speaking_toggle(self, _, is_speaking):
        self.is_speaking = not not is_speaking
        self.toggle_status()

    def toggle_status(self):
        if self.eye_contact and not self.is_speaking:
            self.start()
        else:
            self.pause()

    def processRemote( self, nbOfChannels, nbrOfSamplesByChannel, aTimeStamp, buffer ):
        #print("INF: SpeechRecognitionModule: Processing '%s' channels" % nbOfChannels)

        # calculate a decimal seconds timestamp
        timestamp = float (str(aTimeStamp[0]) + "."  + str(aTimeStamp[1]))

        # put whole function in a try/except to be able to see the stracktrace
        try:

            aSoundDataInterlaced = np.fromstring( str(buffer), dtype=np.int16 )
            aSoundData = np.reshape( aSoundDataInterlaced, (nbOfChannels, nbrOfSamplesByChannel), 'F' )

            # compute RMS, handle autodetection
            if( self.isAutoDetectionEnabled or self.isRecording):

                # compute the rms level on front mic
                rmsMicFront = self.calcRMSLevel(self.convertStr2SignedInt(aSoundData[0]))

                if (rmsMicFront >= self.autoDetectionThreshold):
                    # save timestamp when we last had and RMS > threshold
                    self.lastTimeRMSPeak = timestamp

                    # start recording if we are not doing so already
                    if (self.isAutoDetectionEnabled and self.eye_contact and not self.isRecording):
                        self.startRecording()

            if(self.isRecording):
                # write to buffer
                self.buffer.append(aSoundData)

                if (self.startRecordingTimestamp <= 0):
                    # initialize timestamp when we start recording
                    self.startRecordingTimestamp = timestamp
                elif ((timestamp - self.startRecordingTimestamp) > self.recordingDuration):
                    print('Max recording duration hit')
                    # check how long we are recording
                    self.stopRecordingAndRecognize()

                # stop recording after idle time (and recording at least hold time)
                # lastTimeRMSPeak is 0 if no peak occured
                if (timestamp - self.lastTimeRMSPeak >= self.idleReleaseTime) and (
                        timestamp - self.startRecordingTimestamp >= self.holdTime):
                    # print(('stopping after idle/hold time'))
                    self.stopRecordingAndRecognize()
            else:
                # constantly record into prebuffer for lookahead
                self.preBuffer.append(aSoundData)
                self.preBufferLength += len(aSoundData[0])
                
                # Reset the prebuffer if we are not recording
                self.startRecordingTimestamp = -1

                # remove first (oldest) item if the buffer gets bigger than required
                # removes one block of samples as we store a list of lists...
                overshoot = (self.preBufferLength - self.lookaheadBufferSize)

                if((overshoot > 0) and (len(self.preBuffer) > 0)):
                    self.preBufferLength -= len(self.preBuffer.pop(0)[0])

        except:
            # i did this so i could see the stracktrace as the thread otherwise just silently failed
            traceback.print_exc()

    # processRemote - end

    def calcRMSLevel(self, data):
        rms = (sqrt(mean(square(data))))
        # TODO: maybe a log would be better for threshold?
        #rms = 20 * np.log10(np.sqrt(np.sum(np.power(data, 2) / len(data))))
        return rms

    def version( self ):
        return "1.1"

    # use this method to manually start recording (works with both autodetection enabled or disabled)
    # the recording will stop after the signal is below the threshold for IDLE_RELEASE_TIME seconds,
    # but will at least record for HOLD_TIME seconds
    def startRecording(self):
        if(self.isRecording):
            return

        # if not self.inited:
        #     print("INF: Started, you can speek now\n")
        #     self.inited = True

        # start recording
        self.startRecordingTimestamp = 0
        self.lastTimeRMSPeak = 0
        self.buffer = self.preBuffer

        #self.preBuffer = []

        self.isRecording = True

        return

    def stopRecordingAndRecognize(self):
        if(self.isRecording == False):
            # print("INF: SpeechRecognitionModule.stopRecordingAndRecognize: not recording")
            return

        # print("INF: stopping recording and recognizing")

        # TODO: choose which mic channel to use
        # can we use the sound direction module for this?

        # buffer is a list of nparrays we now concat into one array
        # and the slice out the first mic channel
        slice = np.concatenate(self.buffer, axis=1)[0]

        # initialize preBuffer with last samples to fix cut off words
        # loop through buffer and count samples until prebuffer is full
        # TODO: performance issues!
        if (PREBUFFER_WHEN_STOP):
            sampleCounter = 0
            itemCounter = 0

            for i in reversed(self.preBuffer):
                sampleCounter += len(i[0])

                if(sampleCounter > self.lookaheadBufferSize):
                    break

                itemCounter += 1

            start = len(self.buffer) - itemCounter
            self.preBuffer = self.buffer[start:]
        else:
            # don't copy to prebuffer
            self.preBuffer = []

        # start new worker thread to do the http call and some processing
        # copy slice to be thread safe!
        # TODO: make a job queue so we don't start a new thread for each recognition
        threading.Thread(target=self.recognize, args=(slice.copy(), )).start()

        # reset flag
        self.isRecording = False

        return
    
    def enableAutoDetection(self):
        self.isAutoDetectionEnabled = True
        return

    def disableAutoDetection(self):
        self.isAutoDetectionEnabled = False
        return

    def setLanguage(self, language = DEFAULT_LANGUAGE):
        self.language = language
        return

    # used for RMS calculation
    def convertStr2SignedInt(self, data):
        """
        This function takes a string containing 16 bits little endian sound
        samples as input and returns a vector containing the 16 bits sound
        samples values converted between -1 and 1.
        """

        # from the naoqi sample, but rewritten to use numpy methods instead of for loops

        lsb = data[0::2]
        msb = data[1::2]

        # don't remove the .0, otherwise overflow!
        rms_data = np.add(lsb, np.multiply(msb, 256.0))

        # gives and array that contains -65536 on every position where signedData is > 32768
        sign_correction = np.select([rms_data>=32768], [-65536])

        # add the two to get the correct signed values
        rms_data = np.add(rms_data, sign_correction)

        # normalize values to -1.0 ... +1.0
        rms_data = np.divide(rms_data, 32768.0)

        return rms_data

    def recognize(self, data):
        wav_file = buffer_to_wav_in_memory(data, sample_rate=SAMPLE_RATE)
        result = audio_recoginze(self.stt_url, wav_file, self.stt_route, self.stt_api_key)
        if result:
            self.memory.raiseEvent("SpeechRecognition", result)
            print('Speech Recognition Result:\n================================\n'+result+'\n================================\n')

    def setAutoDetectionThreshold(self, threshold):
        self.autoDetectionThreshold = threshold

    def setIdleReleaseTime(self, releaseTime):
        self.idleReleaseTime = releaseTime

    def setHoldTime(self, holdTime):
        self.holdTime = holdTime

    def setMaxRecordingDuration(self, duration):
        self.recordingDuration = duration

    def setLookaheadDuration(self, duration):
        self.lookaheadBufferSize = duration * SAMPLE_RATE
        self.preBuffer = []
        self.preBufferLength = 0
