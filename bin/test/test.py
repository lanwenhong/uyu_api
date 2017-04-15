#coding: utf-8
import unittest
from zbase.base import logger
from zbase.base.http_client import RequestsClient
from zbase.server.client import HttpClient

import json

log = logger.install('stdout')


class TestUyuInternalApi(unittest.TestCase):

    def setUp(self):
        self.url = ''
        self.send = {}
        self.host = '127.0.0.1'
        self.port = 8087
        self.timeout = 2000
        self.server = [{'addr':(self.host, self.port), 'timeout':self.timeout},]
        self.client = HttpClient(self.server, client_class = RequestsClient)


    @unittest.skip("skipping")
    def test_register(self):
        self.url = '/internal/v1/api/register'
        self.send = {
            'mobile': '13802438742',
            'password': '123456',
            'user_type': 7,
            'nick_name': 'dd',
            'username': 'dd',
            'email': '13802438742@cc.com',
            'store_userid': 51568
        }
        ret = self.client.post(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


    #@unittest.skip("skipping")
    def test_consume_change(self):
        self.url = '/internal/v1/api/consumer_change'
        self.send  = {
            'userid': 1199,
            'store_userid': 1197,
            'training_times': 1
        }
        ret = self.client.post(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


    @unittest.skip("skipping")
    def test_consume_times_stat(self):
        self.url = '/internal/v1/api/consumer_times_stat'
        self.send  = {
            'userid': 1199,
        }
        ret = self.client.get(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


suite = unittest.TestLoader().loadTestsFromTestCase(TestUyuInternalApi)
unittest.TextTestRunner(verbosity=2).run(suite)
