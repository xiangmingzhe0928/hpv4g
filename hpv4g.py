#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
from requests.exceptions import HTTPError
import datetime
from threading import current_thread
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
import argparse
import logging
from miaomiao import MiaoMiao

LOG_NAME = 'hpv.log'

"""
 SecKill HPV
 - 抓取,配置Cookie
 - 获取服务器时间
 - 获取待秒杀疫苗列表
 - 选取秒杀疫苗
 - 计算秒杀开始
 - 多线程并发秒杀
 
"""

# 秒杀结果标志位
KILL_FLAG = False


def sec_kill_task(miao_miao, req_param, proxy=None):
    """
    执行秒杀操作
    :return:
    """
    global KILL_FLAG
    while not KILL_FLAG:
        '''
        服务器做了频率限制 短时间请求太多返回 “操作频繁” 无法确定是 IP限制还是ID限制
        - 考虑加入ip代理处理IP限制 init_ip_proxy_pool()
        '''
        res_json = miao_miao.subscribe(req_param, proxy)
        if res_json['code'] == '0000':
            print(f'{current_thread().name} Kill Success')
            KILL_FLAG = True


def init_ip_proxy_pool(pages: int = 2) -> list:
    """
    填充临时IP代理池。（考虑到秒杀场景瞬时性,提前初始化可用的IP代理 避免秒杀中临时调用API）

    IP代理来源
        1.使用收费的代理商提供
        2.自建IP代理池
            - 爬取免费IP代理
            - 验证IP可用
            - 持久化
            - 定时更新可用IP

    这里直接使用第三方提供的API(避免自建轮子、搭建环境。测试)：https://github.com/jiangxianli/ProxyIpLib
    :return: ip代理池列表
    """
    ip_proxy_res = [MiaoMiao.get_proxy_ip(p)['data']['data'] for p in range(1, pages + 1)]
    return [f'{data["ip"]}:{data["port"]}' for data in list(chain(*ip_proxy_res))]


def run(miao_miao, max_workers=None):
    # 获取疫苗信息(默认选取第一个待秒疫苗)
    vaccines = miao_miao.get_vaccine_list()
    # 获取秒杀人信息
    user = miao_miao.get_user()
    # 秒杀请求参数
    req_param = {'vaccineIndex': '1', 'seckillId': vaccines[0]['id'], 'linkmanId': user[0]['id'],
                 'idCardNo': user[0]['idCardNo']}
    # 初始化IP代理池
    ip_proxys = init_ip_proxy_pool()
    # 计算秒杀开始剩余毫秒数 startTime - serverNowTime
    _start_time_unix = int(datetime.datetime.strptime(vaccines[0]['startTime'], '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
    if _start_time_unix - MiaoMiao.get_server_time() > 5 * 1000:
        print(f'秒杀还未开始 请在秒杀开始前5秒内执行')
        exit(0)

    # _start_time_unix - get_server_time() 使用本地时间还是服务器时间？
    while _start_time_unix - int(datetime.datetime.now().timestamp() * 1000) > 300:
        pass

    # python3.8 默认max_workers = min(32, os.cpu_count() + 4)
    with ThreadPoolExecutor(max_workers=max_workers) as t:
        ip_proxy_len = len(ip_proxys)
        for i in range(100):
            # 此处并没有使用随机选择代理
            index = i % ip_proxy_len
            t.submit(sec_kill_task, req_param, {'http': None if index == 0 else ip_proxys[index]})


def _get_arguments():
    """
    解析参数
    :return:
    """

    def _valid_int_type(i):
        valid_int = int(i)
        if valid_int < 1:
            raise argparse.ArgumentTypeError(f'invalid int argument:{i}')
        return valid_int

    parser = argparse.ArgumentParser(description='HPV SecKill 疫苗秒杀')
    parser.add_argument('tk', help='名为tk的http header')
    parser.add_argument('cookie', help='http请求cookie')
    parser.add_argument('-mw', '--max_workers', type=_valid_int_type, help='最大线工作线程数 默认使用 min(32, os.cpu_count() + 4)')
    parser.add_argument('-rc', '--region_code', type=int, default='5101', help='区域编码 默认使用成都编码5101')
    parser.add_argument('--log', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别 默认WARNING')
    return parser.parse_args()


if __name__ == '__main__':
    args = _get_arguments()

    logging.basicConfig(handlers=[logging.FileHandler(filename=LOG_NAME,
                                                      encoding='utf-8', mode='a+')],
                        format='%(asctime)s %(message)s',
                        level=getattr(logging, args.log))
    run(MiaoMiao(args.tk, args.cookie), args.region_code)
