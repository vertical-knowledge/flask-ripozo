from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import cProfile
import gc
import pstats
import unittest2

from six.moves import urllib


def profileit(func):
    """
    Decorator straight up stolen from stackoverflow
    """
    def wrapper(*args, **kwargs):
        datafn = func.__name__ + ".profile" # Name the data file sensibly
        prof = cProfile.Profile()
        prof.enable()
        retval = prof.runcall(func, *args, **kwargs)
        prof.disable()
        stats = pstats.Stats(prof)
        stats.sort_stats('tottime').print_stats(20)
        print()
        print()
        stats.sort_stats('cumtime').print_stats(20)
        return retval

    return wrapper


class TestProfile(unittest2.TestCase):
    base_url = 'http://127.0.0.1:6000/my_resource/hello/'
    runs = 10000

    def setUp(self):
        gc.collect()

    @profileit
    def test_requests(self):
        for i in range(self.runs):
            resp = urllib.request.urlopen(self.base_url)
