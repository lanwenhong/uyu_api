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
from uyubase.uyu import define
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
        Field('store_userid', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('training_times', T_INT, False),
        Field('eyesight_id', T_INT, True, match=r'^([0-9]{0,10})$'),
        Field('device_id', T_INT, True, match=r'^([0-9]{0,10})$'),
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_database('uyu_core')
    def _trans_store_info(self, store_userid):
        # 是不是门店且状态正常
        ret = self.db.select_one(
            table='auth_user',
            fields='*',
            where={
                'id': store_userid,
                'user_type': define.UYU_USER_ROLE_STORE,
            }
        )

        if not ret:
            return False, UAURET.ROLEERR, None

        state = ret.get('state')
        if state == define.UYU_USER_STATE_OK:
            dbret = self.db.select_one(table='stores', fields='*', where={'userid': store_userid})
            if dbret and dbret['is_valid'] == define.UYU_STORE_STATUS_OPEN:
                return True, UAURET.OK, dbret['id']
            else:
                log.debug('find stores info error store_userid=%s', store_userid)
                return False, UAURET.USERERR, None
        else:
            return False, UAURET.USERERR, None


    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data

            store_userid = params.pop('store_userid')
            check, code, store_id = self._trans_store_info(store_userid)
            if not check:
                return error(code)
            params['store_id'] = store_id

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


class ConsumerTimesStat(core.Handler):

    _get_handler_fields = [
        Field('userid', T_INT, False)
    ]

    @with_validator_self
    def _get_handler(self):
        try:
            params = self.validator.data
            consumer_id = params['userid']
            #是不是消费者
            check = self._check_consumer(consumer_id)
            if not check:
                return error(UAURET.ROLEERR)
            #获取次数
            ret = self._query_handler(consumer_id)
            remain_times = ret.get('remain_times') if ret and ret['remain_times'] else 0
            data = {'remain_times': remain_times}
            return success(data)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.DATAERR)


    @with_database('uyu_core')
    def _query_handler(self, consumer_id):
        keep_fields = [
            'sum(remain_times) as remain_times'
        ]
        where = {'userid': consumer_id}
        ret = self.db.select_one(
            table='consumer', fields=keep_fields, where=where
        )
        return ret

    @with_database('uyu_core')
    def _check_consumer(self, consumer_id):
        keep_fields = ['*']
        where = {'id': consumer_id, 'user_type': define.UYU_USER_ROLE_COMSUMER}
        ret = self.db.select_one(table='auth_user', fields=keep_fields, where=where)
        return ret


    def GET(self):
        try:
            data = self._get_handler()
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)
