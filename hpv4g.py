#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
from threading import current_thread
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from itertools import chain
import argparse
import logging
from miaomiao import MiaoMiao
from time import sleep

LOG_NAME = 'trace.log'

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
    _start_time = req_param['startTimeUnx']
    while _start_time - int(datetime.datetime.now().timestamp() * 1000) > 300:
        pass
    global KILL_FLAG
    while not KILL_FLAG:
        res_json = miao_miao.subscribe(req_param, proxy)
        if res_json['code'] == '0000':
            print(f'{current_thread().name} Kill Success')
            KILL_FLAG = True
            return
        sleep(0.1)


def init_ip_proxy_pool(pages: int = 2) -> list:
    """
    填充临时IP代理池。（考虑到秒杀场景瞬时性,提前初始化可用的IP代理 避免秒杀中临时调用API）
    :return: ip代理池列表
    """
    ip_proxy_res = [MiaoMiao.get_proxy_ip(p)['data']['data'] for p in range(1, pages + 1)]
    return [f'{data["ip"]}:{data["port"]}' for data in list(chain(*ip_proxy_res))]


def _build_skill_param(user, vaccines: list) -> list:
    """
    构建秒杀请求
    :param user: 疫苗接种人(必须是接种人信息)
    :param vaccines: (可秒杀疫苗列表)
    :return: 请求参数对象列表
    """
    _server_time_unix = MiaoMiao.get_server_time()
    _start_time_unix = None
    params = []
    for v in vaccines:
        _start_time_unix = int(datetime.datetime.strptime(v['startTime'], '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
        # 过滤秒杀还未开始的疫苗
        if _start_time_unix - _server_time_unix > 5 * 1000:
            logging.debug(f'{v["name"]},startTime:{v["startTime"]};秒杀还未开始')
            continue
        params.append({'vaccineIndex': '1', 'seckillId': v['id'], 'linkmanId': user['id'], 'idCardNo': user['idCardNo'],
                       'startTimeUnx': _start_time_unix})
    return params


def run(miao_miao, max_workers=None, single=False):
    # 获取疫苗信息(默认选取第一个待秒疫苗)
    vaccines = miao_miao.get_vaccine_list()
    # 获取秒杀人信息
    user = miao_miao.get_user()
    # 选取秒杀即将开始的疫苗列表
    params = _build_skill_param(user[0], vaccines)
    if not params:
        print('秒杀还未开始,请开始前5S执行')
        exit(0)

    params = params if single else params[:1]
    # 初始化IP代理池
    ip_proxys = init_ip_proxy_pool()

    # python3.8 默认max_workers = min(32, os.cpu_count() + 4)
    with ThreadPoolExecutor(max_workers=max_workers) as t:
        ip_proxy_len = len(ip_proxys)
        # [t.submit(sec_kill_task, req_param, {'http': None if i % ip_proxy_len == 0 else ip_proxys[i % ip_proxy_len]})
        #  for i in range(20)]
        fs = []
        for i in range(max_workers + 5):
            # 此处并没有使用随机选择代理
            index = i % ip_proxy_len
            fs.append(
                t.submit(sec_kill_task, params[i % len(params)], {'http': None if index == 0 else ip_proxys[index]}))

        # 30S后结束任务
        wait(fs, 30, return_when=FIRST_COMPLETED)
        global KILL_FLAG
        KILL_FLAG = True

    print('-----DONE----')


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
    parser.add_argument('-sp', '--single_point', action='store_true', help='只秒杀单个疫苗[即所有线程秒杀同一个疫苗] 默认不开启该参数则所有线程分配秒杀所有可秒杀疫苗')
    parser.add_argument('--log', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别 默认WARNING')
    return parser.parse_args()


if __name__ == '__main__':
    args = _get_arguments()
    logging.basicConfig(handlers=[logging.FileHandler(filename=LOG_NAME,
                                                      encoding='utf-8', mode='a+')],
                        format='%(asctime)s %(message)s',
                        level=getattr(logging, args.log))
    run(MiaoMiao(args.tk, args.cookie), args.region_code, args.single_point)
