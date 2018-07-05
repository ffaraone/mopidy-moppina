from __future__ import unicode_literals

import logging
import os

import handlers
import tornado.web
from mopidy import config, ext

__version__ = '0.1.10'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Moppina'
    ext_name = 'moppina'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        # TODO: Comment in and edit, or remove entirely
        #schema['username'] = config.String()
        #schema['password'] = config.Secret()
        return schema

    def setup(self, registry):
        from .frontend import MoppinaFrontend
        registry.add('frontend', MoppinaFrontend)
        registry.add('http:app', {
            'name': self.ext_name,
            'factory': moppina_factory
        })


def moppina_factory(config, core):

    path = os.path.join( os.path.dirname(__file__), 'static')
    
    return [
        (r'/api/([^/]*)', handlers.HttpHandler, {
            'core': core,
            'config': config
        }),
        (r'/(.*)', tornado.web.StaticFileHandler, {
            'path': path,
            'default_filename': 'index.html'
        }),
    ]
