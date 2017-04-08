# -*- coding: utf-8 -*-
from handler import ping
from handler import op
urls = (
    ('^/ping$', ping.Ping),
    ('^/internal/v1/api/register$', op.RegisterHandler),
    ('^/internal/v1/api/consumer_change$', op.ConsumerTimesHandler),
)
