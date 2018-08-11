import threading
import time
import numpy as np
import math
import subprocess
import random

from PIL import Image
from subprocess import Popen, PIPE
from Adafruit_AMG88xx import Adafruit_AMG88xx
from colour import Color

MINTEMP = 10.0
MAXTEMP = 40.0
COLORDEPTH = 1024

INPUT_FPS = 60
OUTPUT_FPS = 30

class StreamProcess(object):

    _FFMPEG_PROCESS = None
    _SENSOR_THREAD = None
    _IMAGE_THREAD = None
    _SENSOR = None
    _STOP = False
    _START_ARGS = None

    _COLORS = None

    _PIXEL_BUFFER_LOCK = threading.Lock()
    _PIXEL_BUFFER = []

    def __init__(self):
        blue = Color("indigo")
        colors = list(blue.range_to(Color("red"), COLORDEPTH))
        self._COLORS = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]
        return

    def start(self, ffmpeg, target):
        self._START_ARGS = [ffmpeg, target]
        self._STOP = False
        self._SENSOR = Adafruit_AMG88xx()
        self._FFMPEG_PROCESS = Popen([
                ffmpeg, 
                '-y',
                '-f', 'image2pipe', 
                "-c:v", "mjpeg",
                #'-framerate', str(INPUT_FPS),
                '-i', '-',
                '-f', 'mpegts',
                '-c:v', 'mpeg1video',
                '-b:v', '0',
                '-bf', '0',
                '-r', str(OUTPUT_FPS),
                target
            ], 
            #-f mpegts -c:v mpeg1video -b:v 100k -bf 0 http://192.168.1.245:8081/secret
            stdin=subprocess.PIPE)
        self._SENSOR_THREAD = threading.Thread(target=self.sensorLoop)
        self._SENSOR_THREAD.start()
        self._IMAGE_THREAD = threading.Thread(target=self.imageLoop)
        self._IMAGE_THREAD.start()
        return

    def stop(self):
        self._STOP = True
        if self._FFMPEG_PROCESS:
            try:
                self._FFMPEG_PROCESS.stdin.write("\x03")
                self._FFMPEG_PROCESS.stdin.close()
                self._FFMPEG_PROCESS.wait()
                self._FFMPEG_PROCESS = None
            except:
                pass
        if self._SENSOR_THREAD:
            try:
                if self._SENSOR_THREAD.isAlive():
                    self._SENSOR_THREAD.join()
                self._SENSOR_THREAD = None
            except:
                pass
        if self._IMAGE_THREAD:
            try:
                if self._IMAGE_THREAD.isAlive():
                    self._IMAGE_THREAD.join()
                self._IMAGE_THREAD = None
            except:
                pass
        return

    def restart(self):
        self.stop()
        self.start(*self._START_ARGS)

    def imageLoop(self):
        time.sleep(1)
        try:
            while not self._STOP:            
                start = time.time()
                self._PIXEL_BUFFER_LOCK.acquire()
                if len(self._PIXEL_BUFFER) == 0: 
                    continue
                
                pixelBuffer = self._PIXEL_BUFFER[:]
                self._PIXEL_BUFFER = []
                self._PIXEL_BUFFER_LOCK.release()

                s = int(len(pixelBuffer[0])**(1/2.0))

                mean = np.mean(pixelBuffer, axis=0)
                mean = [(p -MINTEMP)/(MAXTEMP-MINTEMP) for p in mean]
                colored = np.reshape(mean,(s,s))

                image = Image.fromarray(np.uint8(colored * 255) , 'L')
                image.save(self._FFMPEG_PROCESS.stdin, 'jpeg')
                end = time.time()
                sleepTime = (1.0/INPUT_FPS) - (end - start)
                if sleepTime > 0:
                    time.sleep(sleepTime)
        except Exception as e:
            print (e)
            self.restart()
        return

    def sensorLoop(self):      
        try:  
            time.sleep(3)
            while not self._STOP:
                pixels = self._SENSOR.readPixels()
                
                self._PIXEL_BUFFER_LOCK.acquire()
                self._PIXEL_BUFFER.append(pixels)
                self._PIXEL_BUFFER_LOCK.release()
                
        except Exception as e:
            print (e)
            self.restart()
        return