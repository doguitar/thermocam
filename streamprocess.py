import threading
import multiprocessing
import time
import subprocess
import numpy as np

from PIL import Image
from Adafruit_AMG88xx import Adafruit_AMG88xx
from colour import Color

COLORDEPTH = 1024

OUTPUT_FPS = 5
INPUT_FPS = OUTPUT_FPS*10

class StreamProcess(object):

    _ffmpeg_process = None
    _sensor_timer = None
    _image_timer = None
    _sensor = None
    _stop = False
    _start_args = None

    _colors = None

    _mintemp = 10.0
    _maxtemp = 32.0

    _pixel_buffer_lock = threading.Lock()
    _pixel_buffer_event = threading.Event()
    _pixel_buffer = [_mintemp, _mintemp, _maxtemp, _maxtemp]


    _fakedata = [_mintemp+i for i in range(8*8)]

    def __init__(self):
        blue = Color("indigo")
        colors = list(blue.range_to(Color("red"), COLORDEPTH))
        self._colors = [(int(c.red * 255), int(c.green * 255),
                         int(c.blue * 255)) for c in colors]
        return

    def start(self, ffmpeg, target):
        self._start_args = [ffmpeg, target]
        self._stop = False
        try:
            self._sensor = Adafruit_AMG88xx()
        except: 
            pass
        self._ffmpeg_process = subprocess.Popen([
            ffmpeg,
            '-y',            
            '-f', 'image2pipe',
            "-c:v", "mjpeg",
            '-framerate', str(OUTPUT_FPS),
            '-i', '-',
            '-f', 'mpegts',
            '-c:v', 'mpeg1video',
            '-b:v', '0',
            '-bf', '0',
            '-q', '2',
            '-r', str(OUTPUT_FPS),
            '-g', '1',
            '-bufsize', '2024k',
            '-maxrate', '1024k',
            '-strict', '-1',
            target
        ], stdin=subprocess.PIPE)
        self._pixel_buffer_event.clear()
        self._sensor_timer = PerpetualTimer(1.0/INPUT_FPS, self.read_sensor)
        self._sensor_timer.start()
        self._image_timer = PerpetualTimer(1.0/INPUT_FPS, target=self.render_image)
        self._image_timer.start()
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
        if self._sensor_timer:
            try:
                self._sensor_timer.cancel()
                self._sensor_timer = None
            except:
                pass
        if self._image_timer:
            try:
                self._image_timer.cancel()
                self._image_timer = None
            except:
                pass
        return

    def restart(self):
        self.stop()
        self.start(*self._start_args)

    def render_image(self):
        try:
            self._pixel_buffer_lock.acquire()
            pixelbuffer = self._pixel_buffer[:]
            self._pixel_buffer_lock.release()

            size = int(len(pixelbuffer)**(1 / 2.0))
            size = (size, size)

            pixelbuffer = [(p - self._mintemp) / (max(self._maxtemp - self._mintemp, 1)) for p in pixelbuffer]
            pixelbuffer = [self._colors[int(max(0, min(x, 1)) * COLORDEPTH)-1] for x in pixelbuffer]
            frame = Image.new('RGB', size)
            frame.putdata(pixelbuffer)
            frame.save(self._ffmpeg_process.stdin, 'jpeg')
        except Exception as ex:
            print (ex)
            self.restart()
        return

    def read_sensor(self):
        try:
            if self._sensor:
                pixels = self._sensor.readPixels()
            else:
                self._fakedata.append(self._fakedata.pop(0))
                pixels = self._fakedata

            self._pixel_buffer_lock.acquire()
            self._pixel_buffer = pixels
            self._pixel_buffer_lock.release()

        except Exception as ex:
            print (ex)
            self.restart()
        return


class PerpetualTimer(object):

    def __init__(self, timespan, target):
        self._timespan = timespan
        self._target = target
        self._thread = threading.Thread(target=self.handle_function)
        self._timer = threading.Thread(target=self.timer)
        self._cancel = False
        self._timer_event = threading.Event()


    def handle_function(self):
        while not self._cancel:
            self._timer_event.wait()
            self._timer_event.clear()
            self._target()

    def timer(self):
        while not self._cancel:
            time.sleep(self._timespan)
            self._timer_event.set()

    def start(self):
        self._timer.start()
        self._thread.start()

    def cancel(self):
        self._cancel = True
        self._thread.join()
        self._timer.join()