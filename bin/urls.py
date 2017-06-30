# -*- coding: utf-8 -*-
from handler import ping
from handler import op
urls = (
    ('^/ping$', ping.Ping),
    # 用户注册接口
    ('^/internal/v1/api/register$', op.RegisterHandler),
    # 消费者次数使用接口
    ('^/internal/v1/api/consumer_change$', op.ConsumerTimesHandler),
    # 统计消费者所有门店总的剩余次数
    ('^/internal/v1/api/consumer_times_stat$', op.ConsumerTimesStat),
    # 设备信息
    ('^/v1/device/info$', op.DeviceInfoHandler),
    # 商户对应的设备
    ('^/v1/merchant/device_info$', op.MerchantDeviceInfoHandler),
    # 消费者数据
    ('^/v1/consumer/list$', op.ConsumerListHandler),
    # 更新用户数据
    ('^/v1/user/update$', op.ModifyUserInfoHandler),
    # 校验Token
    ('^/v1/token/verify$', op.TokenVerifyHandler),

)
