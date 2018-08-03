
import threading
import time
import numpy as np
import math
from PIL import Image
from subprocess import Popen, PIPE
from Adafruit_AMG88xx import Adafruit_AMG88xx
from colour import Color

MINTEMP = 10.0
MAXTEMP = 40.0
COLORDEPTH = 1024

INPUT_FPS = 120
OUTPUT_FPS = 30

class StreamProcess(object):
    
    _FFMPEG_PROCESS = None
    _SENSOR_THREAD = None
    _IMAGE_THREAD = None
    _SENSOR = None
    _STOP = False

    _COLORS = None
    
    _PIXEL_BUFFER_LOCK = threading.Lock()
    _PIXEL_BUFFER = []

    def __init__(self):
        blue = Color("indigo")
        colors = list(blue.range_to(Color("red"), COLORDEPTH))
        self._COLORS = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]
        return

    def start(self, target):
        self._STOP = False
        self._SENSOR = Adafruit_AMG88xx()
        self._FFMPEG_PROCESS = Popen([
            'ffmpeg', 
            '-y', 
            '-f', 'image2pipe', 
            '-vcodec', 'mjpeg', 
            '-r', str(INPUT_FPS), 
            '-i', '-', 
            '-vcodec', 'mpeg4', 
            '-qscale', '5', 
            '-r', str(OUTPUT_FPS),
            target], stdin=PIPE)
        self._SENSOR_THREAD = threading.Thread(target=self.sensorLoop)
        self._SENSOR_THREAD.start()
        self._IMAGE_THREAD = threading.Thread(target=self.imageLoop)
        self._IMAGE_THREAD.start()
        return

    def stop(self):
        self._STOP = True
        self._FFMPEG_PROCESS.stdin.close()
        self._FFMPEG_PROCESS.wait()
        self._FFMPEG_PROCESS = None
        self._SENSOR_THREAD.join()
        self._SENSOR_THREAD = None
        return

    def imageLoop(self):
        time.sleep(1)
        while not self._STOP:
            self._PIXEL_BUFFER_LOCK.acquire()
            if len(self._PIXEL_BUFFER) == 0: continue
            
            pixelBuffer = self._PIXEL_BUFFER[:]
            self._PIXEL_BUFFER = []
            self._PIXEL_BUFFER_LOCK.release()

            s = len(pixelBuffer[0])**(1/2.0)

            mean = np.mean(pixelBuffer, axis=0)

            image = Image.fromarray(np.split(mean, s))
            image.save(self._FFMPEG_PROCESS.stdin, 'JPEG')
            time.sleep(1.0/INPUT_FPS)
        return

    def sensorLoop(self):
        while not self._STOP:
            pixels = [MINTEMP + (i/16.0) * (MAXTEMP-MINTEMP) for i in range(0, 16)] #self._SENSOR.readPixels()
            pixels = [map(p, MINTEMP, MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]
            self._PIXEL_BUFFER_LOCK.acquire()
            self._PIXEL_BUFFER.append(pixels)
            self._PIXEL_BUFFER_LOCK.release()
        return