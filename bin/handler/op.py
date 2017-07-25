# -*- coding: utf-8 -*-
import redis
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
from config import redis_url
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
            flag = self.check_name_len(params)
            if not flag:
                return error(UAURET.PARAMERR, respmsg=u'长度在6-16位')
            store_userid = params.pop('store_userid')
            log.debug('RegisterHandler store_userid=%s', store_userid)
            user_type = params['user_type']
            if user_type == define.UYU_USER_ROLE_COMSUMER:
                if store_userid:
                    check, code, store_id = self._trans_store_info(store_userid)
                    log.debug('check=%s, code=%s, store_id=%s', check, code, store_id)
                    if not check:
                        return error(code)
                else:
                    store_id = 0
                flag, userid = uop.internal_user_register_with_consumer(params, store_id)
                log.debug('internal_user_register_with_consumer flag=%s, userid=%s', flag, userid)
            else:
                flag, userid = uop.internal_user_register(params)
                log.debug('internal_user_register flag=%s, userid=%s', flag, userid)
            if flag:
                return success({'userid': userid})
            else:
                return error(UAURET.PHONENUMEXIST)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)


    def check_name_len(self, params):
        flag = True
        key_check = ['username']
        for key in key_check:
            if params.has_key(key) and params[key]:
                length = len(params[key])
                if length < 6 or length > 16:
                    log.warn('key=%s|value=%s|length=%s not in range(6, 16)', key, params[key], length)
                    flag = False
                    break
        return flag


    @with_database('uyu_core')
    def _trans_store_info(self, store_userid):
        # 是不是门店或者医院且状态正常
        ret = self.db.select_one(
            table='auth_user',
            fields='*',
            where={
                'id': store_userid,
                'user_type': ('in', (define.UYU_USER_ROLE_STORE, define.UYU_USER_ROLE_HOSPITAL)),
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
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        ret = self._post_handler()
        self.write(ret)



class ConsumerTimesHandler(core.Handler):
    _post_handler_fields = [
        Field('userid', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('store_userid', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('training_times', T_INT, False),
        Field('eyesight_id', T_INT, True, match=r'^([0-9]{0,10})$'),
        Field('device_id', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('train_id', T_INT, True, match=r'^([0-9]{0,10})$'),
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_database('uyu_core')
    def _trans_store_info(self, store_userid):
        # 是不是门店或者医院且状态正常
        ret = self.db.select_one(
            table='auth_user',
            fields='*',
            where={
                'id': store_userid,
                # 'user_type': define.UYU_USER_ROLE_STORE,
                'user_type': ('in', (define.UYU_USER_ROLE_STORE, define.UYU_USER_ROLE_HOSPITAL)),
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

    @with_database('uyu_core')
    def check_store_device(self, store_id, device_id):
        ret = self.db.select_one(table='device', fields='*', where={'id': device_id, 'store_id': store_id})
        return ret

    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data
            userid = params.get('userid')
            device_id = params.get('device_id')
            store_userid = params.pop('store_userid')
            check, code, store_id = self._trans_store_info(store_userid)
            if not check:
                return error(code)
            params['store_id'] = store_id

            # 添加设备是不是绑定门店且匹配
            flag = self.check_store_device(store_id, device_id)
            if not flag:
                log.debug('store_id=%d and device_id=%d not bind', store_id, device_id)
                return error(UAURET.STOREDEVICEERR)

            cc = ConsumerTimesChange()
            ret, record_id = cc.do_sub_times(params)
            # if ret == UYU_OP_ERR:
            #     return error(UAURET.ORDERERR)
            if ret != UYU_OP_OK:
                return error(ret)
            ret = self._get_remain_times(userid, store_id)

            # if not ret:
            #     result = {'record_id': record_id, 'remain_times': 0}
            # else:
            #     ret['record_id'] = record_id
            #     result = ret
            # return success(result)
            if not ret:
                ret = {'record_id': record_id, 'remain_times': 0}
            else:
                remain_times = ret.get('remain_times')
                if not remain_times:
                    ret['remain_times'] = 0
                else:
                    ret['remain_times'] = int(remain_times)
                ret['record_id'] = record_id
            return success(ret)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)

    @with_database('uyu_core')
    def _get_remain_times(self, userid, store_id):
        # ret = self.db.select_one(table='consumer', fields='remain_times', where={'userid': userid, 'store_id': store_id})
        ret = self.db.select_one(table='consumer', fields='sum(remain_times) as remain_times', where={'userid': userid, 'store_id': ('in', [store_id, 0])})
        log.debug('func=%s|ret=%s', '_get_remain_times', ret)
        return ret


    def POST(self, *args):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
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
            #是不是消费者或者视光师
            check = self._check_consumer(consumer_id)
            if not check:
                return error(UAURET.ROLEERR)
            #获取次数
            ret, buy_ret, store_ret = self._query_handler(consumer_id)
            remain_times = int(ret.get('remain_times')) if ret and ret['remain_times'] else 0
            buy_times = int(buy_ret.get('buy_times')) if buy_ret and buy_ret['buy_times'] else 0
            data = {'remain_times': remain_times, 'buy_times': buy_times, 'stores': store_ret}
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

        buy_keep_fields = [
            'sum(training_times) as buy_times'
        ]
        buy_where = {
            'busicd': define.BUSICD_CHAN_ALLOT_TO_COSUMER,
            'consumer_id': consumer_id,
            'status': define.UYU_ORDER_STATUS_SUCC
        }
        buy_ret = self.db.select_one(
            table='training_operator_record', fields=buy_keep_fields, where=buy_where
        )

        store_ret = self.db.select(
            table='consumer', fields=['remain_times', 'store_id'], where={'userid': consumer_id}
        )

        if store_ret:
            for item in store_ret:
                store_id = item['store_id']
                if store_id == 0:
                    item['store_name'] = '全平台'
                else:
                    result = self.db.select_one(table='stores', fields='store_name', where={'id': item['store_id']})
                    item['store_name'] = result.get('store_name') if result else ''


        return ret, buy_ret, store_ret

    @with_database('uyu_core')
    def _check_consumer(self, consumer_id):
        keep_fields = ['*']
        where = {'id': consumer_id, 'user_type': ('in', (define.UYU_USER_ROLE_COMSUMER, define.UYU_USER_ROLE_EYESIGHT))}
        ret = self.db.select_one(table='auth_user', fields=keep_fields, where=where)
        return ret


    def GET(self):
        try:
            self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
            data = self._get_handler()
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)



class DeviceInfoHandler(core.Handler):

    _get_handler_fields = [
        Field('device_id', T_INT, True),
        Field('blooth_tag', T_STR, True)
    ]

    def _get_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _get_handler(self):
        try:
            params = self.validator.data
            device_id = params['device_id']
            blooth_tag = params['blooth_tag']
            if device_id == '' and blooth_tag == '':
                log.debug('device_id and blooth_tag all null')
                return error(UAURET.DATAERR)
            ret = self._query_handler(device_id, blooth_tag)
            if not ret:
                log.debug('device_id or blooth_tag error device_id=%s, blooth_tag=%s', device_id, blooth_tag)
                return error(UAURET.DATAERR)
            data = self._trans_record(ret)
            return success(data)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.DATAERR)

    @with_database('uyu_core')
    def _query_handler(self, device_id, blooth_tag):
        keep_fields = '*'
        if device_id:
            ret = self.db.select_one(table='device', fields=keep_fields, where={'id': device_id})
        elif blooth_tag:
            ret = self.db.select_one(table='device', fields=keep_fields, where={'blooth_tag': blooth_tag})
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
            self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
            data = self._get_handler()
            log.debug('ret data=%s', data)
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)


class MerchantDeviceInfoHandler(core.Handler):

    _get_handler_fields = [
        Field('store_userid', T_INT, False),
        Field('channel_userid', T_INT, True)
    ]


    @with_validator_self
    def _get_handler(self):
        try:
            params = self.validator.data
            store_userid = params['store_userid']
            channel_userid = params['channel_userid']
            store_id = self._query_store_id(store_userid)
            if channel_userid not in ['', None]:
                channel_id = self._query_channel_id(channel_userid)
            else:
                channel_id = None

            ret = self._query_handler(store_id, channel_id)
            if not ret:
                log.debug('store_id or channel_id error store_id=%s, channel_id=%s', store_id, channel_id)
                return success([])
            return success(ret)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.DATAERR)

    @with_database('uyu_core')
    def _query_store_id(self, store_userid):
        ret = self.db.select_one(table='stores', fields='*', where={'userid': store_userid})
        return ret['id'] if ret else 0

    @with_database('uyu_core')
    def _query_channel_id(self, channel_userid):
        ret = self.db.select_one(table='channel', fields='*', where={'userid': channel_userid})
        return ret['id'] if ret else 0

    @with_database('uyu_core')
    def _query_handler(self, store_id, channel_id=None):
        keep_fields = ['id', 'device_name', 'hd_version', 'blooth_tag', 'scm_tag', 'status']
        where = {'store_id': store_id}
        if channel_id:
            where.update({'channel_id': channel_id})
        ret = self.db.select(table='device', fields=keep_fields, where=where)
        return ret


    def GET(self):
        try:
            self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
            data = self._get_handler()
            log.debug('ret data=%s', data)
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)


class ConsumerListHandler(core.Handler):

    _get_handler_fields = []

    @with_validator_self
    def _get_handler(self):
        try:
            ret = self._query_handler()
            data = self._trans_record(ret)
            return success(data)
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.DATAERR)


    @with_database('uyu_core')
    def _query_handler(self):
        ret = self.db.select(table='consumer', fields='userid')
        return ret

    def _trans_record(self, data):
        result = []
        if not data:
            return []

        for item in data:
            result.append(item['userid'])

        return list(set(result))


    def GET(self):
        try:
            self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
            data = self._get_handler()
            log.debug('ret data=%s', data)
            return data
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.SERVERERR)


class ModifyUserInfoHandler(core.Handler):
    _post_handler_fields = [
        Field('userid', T_INT, False, match=r'^([0-9]{0,10})$'),
        Field('phone_num', T_REG, False, match=r'^([0-9]{11})$'),
        Field('login_name', T_STR, True),
        Field('nick_name', T_STR, True),
        Field('username', T_STR, True),

    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data
            userid = params.pop('userid')
            if not params.get('username'):
                params.pop('username')
            if not params.get("login_name"):
                params.pop("login_name")
            if not params.get("nick_name"):
                params.pop("nick_name")

            ret = self._update_user(userid, params)
            if ret != UYU_OP_OK:
                return error(ret)

            return success({})
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            if e[0] == 1062:
                return error(UAURET.MODIFYUSERINFOERR)
            return error(UAURET.REQERR)

    @with_database('uyu_core')
    def _update_user(self, userid, data):
        now = datetime.datetime.now()
        data.update({'utime': now})
        ret = self.db.update(table='auth_user', values=data, where={'id': userid})
        log.debug('update user info userid=%d, data=%s, ret=%d', userid, data, ret)
        if ret == 0:
            return UAURET.MODIFYUSERINFOERR
        return UYU_OP_OK


    def POST(self, *args):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        ret = self._post_handler()
        self.write(ret)


class TokenVerifyHandler(core.Handler):

    _post_handler_fields = [
        Field('token', T_STR, False),
    ]

    def _post_handler_errfunc(self, msg):
        return error(UAURET.PARAMERR, respmsg=msg)

    @with_validator_self
    def _post_handler(self):
        try:
            params = self.validator.data
            token = params.get('token')
            self.redis_pool = redis.ConnectionPool.from_url(redis_url)
            self.client = redis.StrictRedis(connection_pool=self.redis_pool)
            value = self.client.get(token)
            self.redis_pool.disconnect()
            log.debug('token=%s|value=%s', token, value)
            if not value:
                return error(UAURET.DATAERR)
            return success({})
        except Exception as e:
            log.warn(e)
            log.warn(traceback.format_exc())
            return error(UAURET.REQERR)

    def POST(self, *args):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        ret = self._post_handler()
        self.write(ret)
