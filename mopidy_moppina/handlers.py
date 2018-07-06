from __future__ import unicode_literals

import json
import logging
from pprint import pformat
import requests

import tornado.web

logger = logging.getLogger(__name__)

SIZE_TABLE = {
    '': {
        'width': 300,
        'height': 300
    },
    'small': {
        'width': 300,
        'height': 300
    },
    'medium': {
        'width': 300,
        'height': 300
    },
    'large': {
        'width': 300,
        'height': 300
    },
    'extralarge': {
        'width': 300,
        'height': 300
    },
    'mega': {
        'width': 300,
        'height': 300
    }
}



class HttpHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization, Client-Security-Token, Accept-Encoding")        

    def initialize(self, core, config):
        self.core = core
        self.config = config

        self.lastfm_key = 'd766f7c820cd47404b325ab3e5c4fe0a'
        self.lastfm_endpoint = 'http://ws.audioscrobbler.com/2.0/'

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

    def get_art(self, artist, album=None):
        ret = []
        payload = {
            'api_key': self.lastfm_key,
            'method': 'artist.getinfo' if not album else 'album.getinfo',
            'format': 'json',
            'artist': artist
        }
        if album:
            payload['album'] = album
        

        res = requests.get(self.lastfm_endpoint, params=payload)

        if res.status_code == 200:
            data = res.json()
            key = 'artist' if not album else 'album'
            for img in data.get(key, {}).get('image', []):
                try:
                    img_data = dict(uri=img['#text'])
                    img_data.update(SIZE_TABLE[img['size']])
                    ret.append(img_data)
                except:
                    pass
        return ret


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

        uris = json.loads(self.request.body.decode('utf-8'))
        
        # remove toptrack sauce from spotifyweb uris
        toptrack_uri = 'spotifyweb:sauce:artist-toptracks'
        uris = filter(lambda x: toptrack_uri not in x, uris)
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
            lookup_results = self.core.library.lookup(uris=to_query).get()
            for uri, tracks in lookup_results.iteritems():
                logger.info('found %s result for uri %s', len(tracks), 
                            uri)
                if len(tracks) > 0:
                    track = tracks[0]
                    if uri.startswith('local:artist'):
                        artist = next(iter(track.artists)).name
                        results[uri] = self.get_art(artist)
                    elif uri.startswith('local:album') or \
                            uri.startswith('local:track'):
                        artist = next(iter(track.artists)).name
                        album = track.album.name
                        results[uri] = self.get_art(artist, album)
                    else:
                        logger.warning('unsupported uri %s', uri)
        self.write(results)
        self.finish()
