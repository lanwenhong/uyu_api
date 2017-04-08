# -*- coding: utf-8 -*-
import logging
import datetime
import traceback

from zbase.web import core
from zbase.web.validator import with_validator_self, Field, T_REG
from zbase.web.validator import T_INT, T_STR, T_FLOAT
from zbase.base.dbpool import with_database
from uyubase.base.response import success, error, UAURET
from uyubase.base.uyu_user import UUser
from uyubase.uyu.define import UYU_OP_OK, UYU_OP_ERR
from uyubase.base.training_op import ConsumerTimesChange
log = logging.getLogger()


class RegisterHandler(core.Handler):

    _post_handler_fields = [
        Field('mobile', T_REG, False, match=r'^(1\d{10})$'),
        Field('nick_name', T_STR, True),
        Field('username', T_STR, True),
        Field('password', T_STR, False),
        Field('user_type', T_INT, False, match=r'^([1-7]{1})$'),
        Field('email', T_STR, True, match=r'^[a-zA-Z0-9_\-\'\.]+@[a-zA-Z0-9_]+(\.[a-z]+){1,2}$'),
        Field('sex', T_INT, True, match=r'^([0-1]{1})$')
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)


    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data
            uop = UUser()
            flag, userid = uop.internal_user_register(params)
            if flag:
                return success({'userid': userid})
            else:
                return error(UAURET.DATAEXIST)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)

    def POST(self, *args):
        ret = self._post_handler()
        self.write(ret)



class ConsumerTimesHandler(core.Handler):
    _post_handler_fields = [
        Field('userid', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('store_id', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('training_times', T_INT, False),
        Field('eyesight_id', T_INT, True, match=r'^([0-9]{0,10})$'),
        Field('device_id', T_INT, True, match=r'^([0-9]{0,10})$'),
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data
            cc = ConsumerTimesChange()
            ret = cc.do_sub_times(params)
            if ret == UYU_OP_ERR:
                return error(UAURET.ORDERERR)
            return success({})
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)


    def POST(self, *args):
        ret = self._post_handler()
        self.write(ret)
