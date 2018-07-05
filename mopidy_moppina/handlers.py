from __future__ import unicode_literals

import json
import logging
from pprint import pformat

import tornado.web

logger = logging.getLogger(__name__)

class HttpHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization, Client-Security-Token, Accept-Encoding")        

    def initialize(self, core, config):
        self.core = core
        self.config = config

    # Options request
    # This is a preflight request for CORS requests
    def options(self, slug=None):
        self.set_status(204)
        self.finish()
    
    def process_mop_images_response(self, images):
        results = {}
        to_query = []
        for uri, img_list in images.iteritems():
            if len(img_list) > 0:
                img_dicts = []
                for mpimage in img_list:
                    img_dicts.append({
                        'uri': mpimage.uri,
                        'width': mpimage.width,
                        'height': mpimage.height
                    })
                results[uri] = img_dicts
            else:
                to_query.append(uri)
        return results, to_query

    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        def fix_spotifyweb_uris(uri):
            if uri.startswith('spotifyweb:') and uri.count(':') >= 2:
                return ':'.join(['spotify'] + uri.rsplit(':', 2)[1:])
            return uri
        logger.info('Moppina: search for images')

        uris = json.loads(self.request.body.decode('utf-8'))
        uris = map(fix_spotifyweb_uris, uris)
        images = self.core.library.get_images(uris).get()
        results = {}
        to_query = uris
        if len(images) > 0:
            results, to_query = self.process_mop_images_response(images)
        if len(to_query) > 0:
            tracks = self.core.library.lookup(uris=to_query).get()
            logger.info('*' * 50)
            logger.info(tracks)
            logger.info('*' * 50)
        self.write(results)
        self.finish()
