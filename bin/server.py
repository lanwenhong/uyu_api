#!/home/qfpay/python/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import logging
HOME = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HOME), 'conf'))

import urls
from zbase.base import logger
from zbase.base import dbpool
from zbase.base import loader

from zbase.web import core
from zbase.web import cache
from zbase.web import runner
from zbase.web import template

import config

if config.LOGFILE:
    log = logger.install(config.LOGFILE, when='MIDNIGHT')
else:
    log = logger.install('stdout')

template.install(config.template)

config.URLS = urls.urls


def install_db():
    dbpool.install(config.database)

install_db()
app = core.WebApplication(config)


if __name__ == '__main__':
    runner.run_simple(app, host=config.HOST, port=config.PORT)
