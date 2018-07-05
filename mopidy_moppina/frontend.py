from __future__ import unicode_literals
from mopidy.core import CoreListener

import pykka
import logging
import mopidy_moppina

logger = logging.getLogger(__name__)

class MoppinaFrontend(pykka.ThreadingActor, CoreListener):

    def __init__(self, config, core):
        super(MoppinaFrontend, self).__init__()

    def on_start(self):        
        logger.info('Starting Moppina %s', mopidy_moppina.__version__)

    def on_stop(self):
        logger.info('Stopping Moppina %s', mopidy_moppina.__version__)

        
