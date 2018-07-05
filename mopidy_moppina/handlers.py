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

        def chunks(uris, size):
            idx = 0
            while idx < len(uris):
                yield uris[idx:idx+size]
                idx += size 
        
        logger.info('Moppina: search for images')

        req = json.loads(self.request.body.decode('utf-8'))
        uris = req.get('uris', [])
        
        # remove toptrack sauce from spotifyweb uris
        uris = filter(lambda x: 'spotifyweb:sauce:artist-toptracks' not in x, uris)
        # remove other kind of sauce from spotifyweb uris
        uris = map(fix_spotifyweb_uris, uris)

        
        results = {}
        to_query = []
        
        for c in chunks(uris, 10):
            images = self.core.library.get_images(c).get()
            r, q = self.process_mop_images_response(images)
            results.update(r)
            to_query.extend(q)
        if len(to_query) > 0:
            for uri in to_query:
                lookup_results = self.core.library.lookup(uri=uri).get()
                # logger.info('*' * 50)
                # logger.info('lookup results %s', lookup_results) 
                # # for uri, tracks in lookup_results.iteritems():
                # #     logger.info('%s %s', uri, pformat(tracks))
                # logger.info('*' * 50)
        self.write(results)
        self.finish()
