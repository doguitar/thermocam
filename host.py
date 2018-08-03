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
        self._stream_process.start("http://localhost:8081")
        #self._cp_config = {'request.error_response': self.handle_error}
        cherrypy.engine.subscribe('stop', self.__del__)

    def handle_error(self):
        #log_error(cherrypy._cperror.format_exc())
        raise cherrypy.HTTPRedirect("/log")

    def __del__(self):
        self.stop()
        return

    def __get_template(self, template):
        return self.lookup.get_template(template)

    def stop(self):
        self._stream_process.stop()
        return

    @cherrypy.expose
    def index(self):
        return self.__get_template("index.mako").render(
            base=self.url_base)


try:
    print "launching"
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

    app_config = {
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
    host_process = None
    host_process = Host(current_directory, settings)
    cherrypy.tree.mount(host_process, config=app_config)
    cherrypy.engine.start()
    print "launched"
    cherrypy.engine.block()
except Exception as e:
    print e
finally:
    if host_process:
        host_process.__del__()
