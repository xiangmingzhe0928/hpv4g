#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime

import requests
import copy
import logging
from hashlib import md5
import json
import os
from functools import wraps

# disable ssl warnings
requests.packages.urllib3.disable_warnings()

# url
URLS = {
    # 获取代理IP
    "IP_PROXY": "https://ip.jiangxianli.com/api/proxy_ips",
    # 服务器当前时间戳
    "SERVER_TIME": "https://miaomiao.scmttec.com/seckill/seckill/now2.do",
    # 疫苗列表
    "VACCINE_LIST": "https://miaomiao.scmttec.com/seckill/seckill/list.do",
    # 校验库存
    "CHECK_STOCK": "https://miaomiao.scmttec.com/seckill/seckill/checkstock2.do",
    # 接种人信息
    "USER_INFO": "https://miaomiao.scmttec.com/seckill/linkman/findByUserId.do",
    # 秒杀疫苗
    "SEC_KILL": "https://miaomiao.scmttec.com/seckill/seckill/subscribe.do"
}

# common headers
REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat",
    "Referer": "https://servicewechat.com/wxff8cad2e9bf18719/10/page-frame.html",
    "Accept": "application/json, text/plain, */*",
    "Host": "miaomiao.scmttec.com"
}

# ecc_hs盐
ECC_HS_SALT = 'ux$ad70*b'


def cache_json(file_name):
    """
    测试发现在开始秒杀前服务器对非核心秒杀接口做了降级处理(查询列表等接口直接返回502).
    考虑提前缓存疫苗列表 秒杀开始后跳过查询列表等操作 直接调用秒杀接口

    JSON文件缓存Decorator
    :param file_name:
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            fn, suffix = os.path.splitext(file_name)
            _file_name = f'{fn}_{self._region_code}{suffix}'
            # 已缓存从缓存读取
            if os.path.exists(_file_name) and os.path.getsize(_file_name):
                with open(_file_name, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # 未缓存
            data = func(self, *args, **kwargs)
            with open(_file_name, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return data

        return wrapper

    return decorator


class MiaoMiao():
    def __init__(self, tk, cookie, region_code=5101):
        self._region_code = region_code
        self._headers = copy.deepcopy(REQ_HEADERS)
        self._headers['tk'] = tk
        self._headers['cookie'] = cookie

    @staticmethod
    def _get(url, params=None, error_exit=True, **kwargs):
        """
        GET请求. 请求返回错误码(4XX,5XX)时退出
        :param url: 请求路径
        :param params: 请求参数
        :param error_exit:返回4XX 5XX错误时 是否退出
        :param kwargs: 附加信息
        :return: 结果JSON
        """
        try:
            response = requests.get(url, params, **kwargs)
            response.raise_for_status()
        except Exception as err:
            print(f'URL:{url} error occurred{err}')
            logging.error(f'URL:{url} ERROR:{err}')
            if error_exit:
                exit(1)
        else:
            res_json = response.json()
            logging.info(
                f'{url}\n{"-" * 5 + "Request" + "-" * 5}\n{params}\n{"-" * 5 + "Response" + "-" * 5}\n{res_json}\nuseTime:{response.elapsed.total_seconds()}S\n')
            return res_json

    @staticmethod
    def get_server_time():
        """
        获取服务器当前时间戳
        秒杀开始时间由服务器控制
        :return: 服务器时间戳
        """
        res_json = MiaoMiao._get(URLS['SERVER_TIME'], verify=False)
        return res_json['data']

    @staticmethod
    def get_proxy_ip(page=1):
        """
        获取最新可用的代理IP
        IP代理来源
            1.使用收费的代理商提供
            2.自建IP代理池
                - 爬取免费IP代理
                - 验证IP可用
                - 持久化
                - 定时更新可用IP

        这里直接使用第三方提供的API(避免自建轮子、搭建环境。测试)：https://github.com/jiangxianli/ProxyIpLib
        :param page:
        :return:
        """
        return MiaoMiao._get(URLS['IP_PROXY'], params={'page': page, 'country': '中国', 'order_by': 'validated_at'},
                             error_exit=False,
                             verify=False)

    def _get_vaccine_list(self):
        """
        获取待秒杀疫苗列表
        :return:疫苗列表
        """
        # 分页查询可秒杀疫苗 regionCode:5101[四川成都区域编码]
        req_param_list = {'offset': '0', 'limit': '10', 'regionCode': self._region_code}
        res_vaccine = MiaoMiao._get(URLS['VACCINE_LIST'], params=req_param_list, headers=self._headers, verify=False)
        if '0000' != res_vaccine['code']:
            print(res_vaccine['msg'])
            exit(1)

        datas = res_vaccine['data']
        if not datas:
            print(f'---区域:{self._region_code}暂无可秒杀疫苗---')
            _cache_file = f'cache/vaccines_{self._region_code}.json'
            if os.path.exists(_cache_file):
                os.remove(_cache_file)
            exit(0)
        return datas

    @cache_json('cache/vaccines.json')
    def get_vaccine_list_cache(self):
        return self._get_vaccine_list()

    def _get_user(self):
        """
        获取用户信息(从微信小程序入口 使用微信tk和cookie查询指定用户信息)
        :return: 用户信息
        """
        res_json = MiaoMiao._get(URLS['USER_INFO'], headers=self._headers, verify=False)
        if '0000' == res_json['code']:
            return res_json['data']
        print(f'{self._region_code}获取用户信息失败:{res_json}')
        exit(1)

    @cache_json('cache/user.json')
    def get_user_cache(self):
        return self._get_user()

    def subscribe(self, req_param, proxies=None):
        """
        秒杀请求
        :param req_param: 请求参数
        :param proxies: 代理配置
        :return:
        """
        # error_exit=False 忽略Server端使用5XX防爬策略
        self._headers['ecc-hs'] = MiaoMiao._ecc_hs_header(req_param["seckillId"], req_param["linkmanId"])
        return MiaoMiao._get(URLS['SEC_KILL'], params=req_param, error_exit=False, headers=self._headers,
                             proxies=proxies, verify=False)

    @staticmethod
    def _ecc_hs_header(seckill_id, linkman_id):
        """
        构造ecc-hs header
        :param seckill_id: 疫苗ID
        :param linkman_id: 接种人ID
        :return: ecc-hs header

         salt = 'ux$ad70*b';
         md5Str = utilMd5.hexMD5(utilMd5.hexMD5(ms_id + defaultMember.id + st) + salt)
        """
        _ori_md5 = md5(
            f'{seckill_id}{linkman_id}{int(datetime.datetime.now().timestamp() * 1000)}'.encode('utf-8')).hexdigest()
        _md5_salt = md5(f'{_ori_md5}{ECC_HS_SALT}'.encode('utf-8'))
        return _md5_salt.hexdigest()

    def init_data_json(self):
        """
        初始化疫苗数据和接种人数据
        缓存本地
        """
        data_dict = {'user': self._get_user(), 'vaccines': self._get_vaccine_list()}
        for k, v in data_dict.items():
            with open(f'cache/{k}_{self._region_code}.json', 'w', encoding='utf-8') as f:
                json.dump(v, f, ensure_ascii=False, indent=4)
