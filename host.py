#!/usr/bin/env python

import os
import time
import json
import streamprocess
import cherrypy
import numpy
from cherrypy.lib.static import serve_file
from mako.lookup import TemplateLookup

class Host(object):
    _cp_config = None

    url_base = "/"
    base_path = None
    cache_string = 'max-age=432000'
    _stream_process = streamprocess.StreamProcess()

    def __init__(self, base_path, settings):
        self.base_path = base_path
        self.url_base = settings["url_base"]
        self.lookup = TemplateLookup(
            directories=[os.path.join(self.base_path, "html", "templates")])
        self.settings = settings
        self._stream_process.start(settings["ffmpeg"], settings["ffmpeg_output"])
        self._cp_config = {'request.error_response': self.handle_error}
        cherrypy.engine.subscribe('stop', self.__del__)
        return

    def handle_error(self):
        #log_error(cherrypy._cperror.format_exc())
        raise cherrypy.HTTPRedirect("/log")

    def __del__(self):
        self.stop()
        return

    def __get_template(self, template):
        return self.lookup.get_template(template)

    @cherrypy.expose
    def stop(self):
        self._stream_process.stop()
        return

    @cherrypy.expose
    def restart(self):
        self._stream_process.restart()
        return

    @cherrypy.expose
    def start(self):        
        self._stream_process.start(settings["ffmpeg"], settings["ffmpeg_output"])

    @cherrypy.expose
    @cherrypy.tools.etags(autotags=True)
    def js(self, *args):
        path = '/'.join(filter(lambda a: not a == "..", args))
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        cherrypy.response.headers['Cache-Control'] = self.cache_string
        return open(os.path.join(self.base_path, "html", "js", path))

    @cherrypy.expose
    @cherrypy.tools.etags(autotags=True)
    def css(self, *args):
        path = '/'.join(filter(lambda a: not a == "..", args))
        if path.lower().endswith("css"):
            cherrypy.response.headers['Content-Type'] = 'text/css'
        elif path.lower().endswith("png"):
            cherrypy.response.headers['Content-Type'] = 'image/png'
        cherrypy.response.headers['Cache-Control'] = self.cache_string
        return serve_file(os.path.realpath(os.path.join(self.base_path, "html", "css", path)))

    @cherrypy.expose
    def index(self):
        return self.__get_template("index.mako").render(
            base=self.url_base,
            socketAddress="192.168.1.245:8080")


print ("launching")
current_directory = os.path.dirname(os.path.realpath(__file__))

settings_file = os.path.join(current_directory, "settings.json")
settings = {"url_base": "/",
            "port": 4567
            }

if os.path.exists(settings_file):
    with open(settings_file, 'r') as settings_obj:
        settings.update(json.load(settings_obj))
else:
    with open(settings_file, 'w') as settings_obj:
        json.dump(settings, settings_obj, sort_keys=True, indent=1)

CONFIG = {
        '/': {
            'tools.auth_basic.on': False,
            'tools.gzip.on': True,
            'tools.gzip.mime_types': ['text/*', 'image/*', 'application/*', "json/*"]
        }
    }

cherrypy.config.update(
    {
        'server.socket_host': '0.0.0.0', 'server.socket_port': settings["port"], 'thread_pool': 100
    })

#cherrypy.quickstart(Host(current_directory, settings), '/', CONFIG)
HOST_PROCESS = Host(current_directory, settings)
cherrypy.tree.mount(HOST_PROCESS, config=CONFIG)
cherrypy.engine.signals.subscribe()
cherrypy.engine.start()
print("launched")
cherrypy.engine.block()
time.sleep(120)      
