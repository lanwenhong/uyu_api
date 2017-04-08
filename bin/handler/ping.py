# coding=utf-8
from zbase.web import core

class Ping(core.Handler):
    def GET(self):
        self.write('OK')
