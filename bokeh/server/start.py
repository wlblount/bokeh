from __future__ import absolute_import, print_function
import logging
log = logging.getLogger(__name__)
import atexit
import os
import re
import sys
import uuid
import time

from flask import Flask
from six.moves.queue import Queue
from tornado.httpserver import HTTPServer
from tornado import ioloop

from .settings import settings as server_settings
from ..settings import settings as bokeh_settings
from .flask_gzip import Gzip

from bokeh import plotting # imports custom objects for plugin
from bokeh import models, protocol # import objects so that we can resolve them
from bokeh.utils import scale_delta
# this just shuts up pyflakes
models, plotting, protocol
from . import services
from .app import bokeh_app, app
from .configure import (configure_flask, make_tornado_app,
                        register_blueprint, SimpleBokehTornadoApp)

def doc_prepare():
    server_settings.model_backend = {'type' : 'memory'}
    configure_flask()
    register_blueprint()
    return app

http_server = None
def start_redis():
    work_dir = getattr(bokeh_app, 'work_dir', os.getcwd())
    data_file = getattr(bokeh_app, 'data_file', 'redis.db')
    stdout = getattr(bokeh_app, 'stdout', sys.stdout)
    stderr = getattr(bokeh_app, 'stdout', sys.stderr)
    redis_save = getattr(bokeh_app, 'redis_save', True)
    mproc = services.start_redis(pidfilename=os.path.join(work_dir, "bokehpids.json"),
                                 port=bokeh_app.backend.get('redis_port', 6379),
                                 data_dir=work_dir,
                                 data_file=data_file,
                                 stdout=stdout,
                                 stderr=stderr,
                                save=redis_save)
    bokeh_app.redis_proc = mproc

server = None
def make_tornado(config_file=None):
    configure_flask(config_file=config_file)
    register_blueprint()
    tornado_app = make_tornado_app(flask_app=app)
    return tornado_app

def start_simple_server(args=None):
    global server
    configure_flask(config_argparse=args)
    if server_settings.model_backend.get('start-redis', False):
        start_redis()
    register_blueprint()
    tornado_app = make_tornado_app(flask_app=app)
    server = HTTPServer(tornado_app)
    server.listen(server_settings.port, server_settings.ip)
    ioloop.IOLoop.instance().start()

def stop():
    if hasattr(bokeh_app, 'redis_proc'):
        bokeh_app.redis_proc.close()
    server.stop()
    bokehapp = server.request_callback
    bokehapp.stop_threads()
    ioloop.IOLoop.instance().stop()
    ioloop.IOLoop.instance().clear_instance()
