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
        # Field('mobile', T_REG, False, match=r'^(1\d{10})$'),
        Field('mobile', T_REG, False, match=r'^([0-9]{11})$'),
        Field('nick_name', T_STR, True),
        Field('username', T_STR, True),
        Field('password', T_STR, False),
        Field('user_type', T_INT, False, match=r'^([1-7]{1})$'),
        Field('email', T_STR, True, match=r'^[a-zA-Z0-9_\-\'\.]+@[a-zA-Z0-9_]+(\.[a-z]+){1,2}$'),
        Field('sex', T_INT, True, match=r'^([0-1]{1})$'),
        Field('store_userid', T_INT, True)
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _post_handler(self):
        try:
            uop = UUser()
            params = self.validator.data
            store_userid = params.pop('store_userid')
            user_type = params['user_type']
            if store_userid and user_type == define.UYU_USER_ROLE_COMSUMER:
                check, code, store_id = self._trans_store_info(store_userid)
                if not check:
                    return error(code)
                flag, userid = uop.internal_user_register_with_consumer(params, store_id)
            else:
                flag, userid = uop.internal_user_register(params)

            if flag:
                return success({'userid': userid})
            else:
                return error(UAURET.DATAEXIST)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)

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
            log.debug('store_userid error or role error')
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
            log.debug('find stores info state error store_userid=%s', store_userid)
            return False, UAURET.USERERR, None


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

    def _get_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

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
            remain_times = int(ret.get('remain_times')) if ret and ret['remain_times'] else 0
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



class DeviceInfoHandler(core.Handler):

    _get_handler_fields = [
        Field('device_id', T_INT, False)
    ]

    def _get_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _get_handler(self):
        try:
            params = self.validator.data
            device_id = params['device_id']
            ret = self._query_handler(device_id)
            if not ret:
                log.debug('device_id error=%s', device_id)
                return error(UAURET.DATAERR)
            data = self._trans_record(ret)
            return success(data)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.DATAERR)

    @with_database('uyu_core')
    def _query_handler(self, device_id):
        keep_fields = '*'
        ret = self.db.select_one(table='device', fields=keep_fields, where={'id': device_id})
        return ret


    @with_database('uyu_core')
    def _trans_record(self, data):
        log.debug('device origin info data=%s', data)
        channel_id = data.pop('channel_id')
        store_id = data.pop('store_id')
        if channel_id:
            ret = self.db.select_one(table='channel', fields='*', where={'id': channel_id})
            data['channel_id'] = ret.get('userid')
        else:
            data['channel_id'] = 0

        if store_id:
            ret = self.db.select_one(table='stores', fields='*', where={'id': store_id})
            data['store_id'] = ret.get('userid')
        else:
            data['store_id'] = 0

        return data


    def GET(self):
        try:
            data = self._get_handler()
            log.debug('ret data=%s', data)
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)
