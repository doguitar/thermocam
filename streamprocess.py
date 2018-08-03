import Image
import threading

from subprocess import Popen, PIPE



fps, duration = 24, 100
p = Popen(['ffmpeg', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '24', '-i', '-', '-vcodec', 'mpeg4', '-qscale', '5', '-r', '24', 'video.avi'], stdin=PIPE)
for i in range(fps * duration):
    im = Image.new("RGB", (300, 300), (i, 1, 1))
    im.save(p.stdin, 'JPEG')
p.stdin.close()
p.wait()

class StreamProcess(object):
    
    _FFMPEG_PROCESS = None

    def __init__(self):
        return

    def start(self, target):
        self._FFMPEG_PROCESS = Popen([
            'ffmpeg', 
            '-y', 
            '-f', 'image2pipe', 
            '-vcodec', 'mjpeg', 
            '-r', '24', 
            '-i', '-', 
            '-vcodec', 'mpeg4', 
            '-qscale', '5', 
            '-r', '24', 
            target], stdin=PIPE)
        return

    def stop(self):
        return
