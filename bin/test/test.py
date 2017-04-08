#coding: utf-8

from zbase.base import logger
from zbase.base.http_client import RequestsClient
from zbase.server.client import HttpClient

import json

log = logger.install('stdout')


def test_register():
    SERVER   = [{'addr':('127.0.0.1', 8087), 'timeout':2000},]
    client = HttpClient(SERVER, client_class = RequestsClient)
    post_data = {
        'mobile': '13802438719',
        'password': '123456',
        'user_type': 7,
        'nick_name': 'dengcheng',
        'username': 'dengcheng',
        'email': 'xxxx'
    }
    ret = client.post('/internal/v1/api/register', post_data)
    log.info(ret)

def test_consume_change():
    url = '/internal/v1/api/consumer_change'
    SERVER   = [{'addr':('127.0.0.1', 8087), 'timeout':2000},]
    client = HttpClient(SERVER, client_class = RequestsClient)
    post_data  = {
        'userid': 1120,
        'store_id': 54,
        'training_times': 1
    }
    ret = client.post(url, post_data)
    log.info(ret)


if __name__ == '__main__':
    # test_register()
    test_consume_change()
