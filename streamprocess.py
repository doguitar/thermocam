import threading
import time
import subprocess
import numpy as np

from PIL import Image
from Adafruit_AMG88xx import Adafruit_AMG88xx
from colour import Color

COLORDEPTH = 1024

INPUT_FPS = 60
OUTPUT_FPS = 30


class StreamProcess(object):

    _ffmpeg_process = None
    _sensor_thread = None
    _image_thread = None
    _sensor = None
    _stop = False
    _start_args = None

    _colors = None

    _pixel_buffer_lock = threading.Lock()
    _pixel_buffer = []

    _history = [(10, 40) for i in range(120)]

    def __init__(self):
        blue = Color("indigo")
        colors = list(blue.range_to(Color("red"), COLORDEPTH))
        self._colors = [(int(c.red * 255), int(c.green * 255),
                         int(c.blue * 255)) for c in colors]
        return

    def start(self, ffmpeg, target):
        self._start_args = [ffmpeg, target]
        self._stop = False
        self._sensor = Adafruit_AMG88xx()
        self._ffmpeg_process = subprocess.Popen([
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
        ], stdin=subprocess.PIPE)
        self._sensor_thread = threading.Thread(target=self.sensor_loop)
        self._sensor_thread.start()
        self._image_thread = threading.Thread(target=self.image_loop)
        self._image_thread.start()
        return

    def stop(self):
        self._stop = True
        if self._ffmpeg_process:
            try:
                self._ffmpeg_process.stdin.write("\x03")
                self._ffmpeg_process.stdin.close()
                self._ffmpeg_process.wait()
                self._ffmpeg_process = None
            except:
                pass
        if self._sensor_thread:
            try:
                if self._sensor_thread.isAlive():
                    self._sensor_thread.join()
                self._sensor_thread = None
            except:
                pass
        if self._image_thread:
            try:
                if self._image_thread.isAlive():
                    self._image_thread.join()
                self._image_thread = None
            except:
                pass
        return

    def restart(self):
        self.stop()
        self.start(*self._start_args)

    def image_loop(self):
        time.sleep(1)
        try:
            while not self._stop:
                self._pixel_buffer_lock.acquire()
                if len(self._pixel_buffer) == 0:
                    self._pixel_buffer_lock.release()
                    continue

                pixelbuffer = self._pixel_buffer[:]
                self._pixel_buffer = []
                self._pixel_buffer_lock.release()

                s = int(len(pixelbuffer[0])**(1 / 2.0))

                mean = np.mean(pixelbuffer, axis=0)

                self._history.pop(0)
                self._history.append((min(mean), max(mean)))
                self._mintemp = min([x[0] for x in self._history])
                self._maxtemp = max([x[1] for x in self._history])

                mean = [(p - self._mintemp) /
                        (max(self._maxtemp - self._mintemp, 1)) for p in mean]
                colored = np.reshape(mean, (s, s))

                image = Image.fromarray(np.uint8(colored * 255), 'L')
                image.save(self._ffmpeg_process.stdin, 'jpeg')
        except Exception as ex:
            print (ex)
            self.restart()
        return

    def sensor_loop(self):
        try:
            time.sleep(3)
            while not self._stop:
                start = time.time()
                pixels = self._sensor.readPixels()

                self._pixel_buffer_lock.acquire()
                self._pixel_buffer.append(pixels)
                self._pixel_buffer_lock.release()

                end = time.time()
                sleeptime = (1.0 / INPUT_FPS) - (end - start)
                if sleeptime > 0:
                    time.sleep(sleeptime)

        except Exception as ex:
            print (ex)
            self.restart()
        return
