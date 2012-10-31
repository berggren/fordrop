# Copyright (C) 2012 NORDUnet A/S.
# This file is part of fordrop - https://fordrop.org
# See the file 'docs/LICENSE' for copying permission.

__author__ = 'jbn'

import unittest
import string
import random
import ConfigParser
import sys
sys.path.append("/Users/jbn/s/code/fordrop-core")
from fordrop.client import FordropRestClient

class FordropClientTest(unittest.TestCase):
    def setUp(self):
        """ Setup some initial configuration, and initiate a fordrop client object """
        CONFIG_FILENAME = '/Users/jbn/s/code/fordrop-core/fordrop/fordrop.cfg'
        config = ConfigParser.ConfigParser()
        config.read(CONFIG_FILENAME)
        self.url = config.get("client", "base-url")
        self.username = config.get("client", "username")
        self.api_key = config.get("client", "api-key")
        self.fordrop = FordropRestClient(self.url, self.username, self.api_key)

    def test_list_nodes(self):
        """ List nodes, check if return a list """
        self.assertIsInstance(self.fordrop.list_nodes(), list)

    def test_create_node(self):
        """ Create node, check if response code is 201 """
        _name = ''.join(random.sample(string.ascii_lowercase, 16))
        self.assertEqual(self.fordrop.create_node(title=_name, name=_name).status_code, 201)
        self.fordrop.delete_node(node=_name)

    def test_delete_node(self):
        """ Delete node, check if response code is 200 """
        _name = ''.join(random.sample(string.ascii_lowercase, 16))
        self.fordrop.create_node(title=_name, name=_name)
        self.assertEqual(self.fordrop.delete_node(node=_name).status_code, 200)

if __name__ == '__main__':
    unittest.main()
