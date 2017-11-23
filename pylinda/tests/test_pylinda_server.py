from unittest import TestCase

import pylinda

class TestPylindaServer(TestCase):
    def test_is_string(self):
        s = pylinda.server()
        self.assertTrue(isinstance(s, basestring))
        
