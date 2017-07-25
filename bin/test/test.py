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
            'mobile': '13928478231',
            'password': '123456',
            'user_type': 7,
            'nick_name': '张三',
            'username': '1234567890111111',
            'email': '13928478231@cc.com',
            'store_userid': 51568
        }
        ret = self.client.post(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


    # @unittest.skip("skipping")
    def test_consume_change(self):
        self.url = '/internal/v1/api/consumer_change'
        self.send  = {
            'userid': 1199,
            'store_userid': 1197,
            'training_times': 1,
            'device_id': 114
            # 'device_id': 136
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


    @unittest.skip("skipping")
    def test_device_info(self):
        self.url = '/v1/device/info'
        self.send  = {
            #'device_id': 111,
            'scm_tag': 'sm_v1'
        }
        ret = self.client.get(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')

    @unittest.skip("skipping")
    def test_merchant_device_info(self):
        self.url = '/v1/merchant/device_info'
        self.send  = {
            'store_userid': 1197,
            'channel_userid': 1196
        }
        ret = self.client.get(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


    @unittest.skip("skipping")
    def test_consumer_list(self):
        self.url = '/v1/consumer/list'
        self.send  = {}
        ret = self.client.get(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


    @unittest.skip("skipping")
    def test_update_user_info(self):
        self.url = '/v1/user/update'
        self.send  = {
            'login_name': 'dc12345',
            'phone_num': '13802438716',
            'nick_name': 'dc_14567',
            'userid': 1262
        }
        ret = self.client.post(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')

    @unittest.skip("skipping")
    def test_token_verify(self):
        self.url = '/v1/token/verify'
        self.send = {
            # 'token': 'd5872ece-433f-451c-b4cf-fca97f759489'
            'token': 'd5872ece'
        }
        ret = self.client.post(self.url, self.send)
        log.info(ret)
        respcd = json.loads(ret).get('respcd')
        self.assertEqual(respcd, '0000')


suite = unittest.TestLoader().loadTestsFromTestCase(TestUyuInternalApi)
unittest.TextTestRunner(verbosity=2).run(suite)
