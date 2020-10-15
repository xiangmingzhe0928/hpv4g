#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import textwrap
from os import cpu_count
from threading import current_thread
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED
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
    ip_proxy_res = []
    for p in range(1, pages + 1):
        if ipt := MiaoMiao.get_proxy_ip(p):
            ip_proxy_res.append(ipt['data']['data'])
    # ip_proxy_res = [MiaoMiao.get_proxy_ip(p)['data']['data'] for p in range(1, pages + 1)]
    return [f'{data["ip"]}:{data["port"]}' for data in list(chain(*ip_proxy_res))] if ip_proxy_res else ip_proxy_res


def _build_skill_param(user, vaccines: list) -> list:
    """
    构建秒杀请求参数
    :param user: 疫苗接种人(必须是接种人信息)
    :param vaccines: (可秒杀疫苗列表)
    :return: 请求参数对象列表
    """
    _server_time_unix = int(datetime.datetime.now().timestamp() * 1000)  # MiaoMiao.get_server_time()? 是否有必要以服务器时间为准???
    _start_time_unix = None
    params = []
    for v in vaccines:
        # 过滤秒杀已结束的疫苗(约苗会出现已秒杀结束的疫苗长期存在秒杀列表的情况)
        if not v['stock']:
            continue

        # 过滤距秒杀开始大于5S的疫苗
        _start_time_unix = int(datetime.datetime.strptime(v['startTime'], '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
        if _start_time_unix - _server_time_unix > 5 * 1000:
            logging.debug(f'{v["name"]},startTime:{v["startTime"]};秒杀还未开始')
            continue
        # 构造秒杀参数
        params.append({'vaccineIndex': '1', 'seckillId': v['id'], 'linkmanId': user['id'], 'idCardNo': user['idCardNo'],
                       'startTimeUnx': _start_time_unix})
    return params


def run(miao_miao, max_workers=None, single=False, proxy=False):
    # 获取疫苗信息(默认选取第一个待秒疫苗)
    vaccines = miao_miao.get_vaccine_list_cache()
    # 获取秒杀人信息
    user = miao_miao.get_user_cache()
    # 选取秒杀即将开始的疫苗列表
    params = _build_skill_param(user[0], vaccines)
    if not params:
        print('秒杀还未开始,请开始前5S执行')
        exit(0)
    # 是否单点疫苗秒杀
    params = params if not single else params[:1]
    # 是否使用IP代理池
    ip_proxys = [] if not proxy else init_ip_proxy_pool()

    # python3.8 默认max_workers = min(32, os.cpu_count() + 4)
    _params_len = len(params)
    _ip_proxys_len = len(ip_proxys)
    with ThreadPoolExecutor(max_workers=max_workers) as t:
        fs = [t.submit(sec_kill_task, miao_miao, params[i % _params_len],
                       None if not _ip_proxys_len else {
                           'http': None if (index := i % _ip_proxys_len) == 0 else ip_proxys[index]}) for i in
              range(max_workers + 5)]

        # 180S后结束任务
        wait(fs, 180, return_when=FIRST_COMPLETED)
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

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=textwrap.dedent("""\
    HPV SecKill 疫苗秒杀
    暂不支持选择指定疫苗(默认同时秒杀全部可秒杀疫苗 使用-sp开启单个秒杀)
    """))
    parser.add_argument('tk', help='名为tk的http header')
    parser.add_argument('cookie', help='http请求cookie')
    parser.add_argument('-mw', '--max_workers', type=_valid_int_type, default=min(32, cpu_count() + 4),
                        help='最大线工作线程数 默认使用 min(32, os.cpu_count() + 4)')
    parser.add_argument('-rc', '--region_code', type=int, default='5101', help='区域编码 默认使用成都编码5101')
    parser.add_argument('-reload_cache', action='store_true', help='刷新--region_code疫苗列表本地缓存')
    parser.add_argument('-sp', '--single_point', action='store_true',
                        help='只秒杀单个疫苗[即所有线程秒杀同一个疫苗] 默认不开启该参数则所有线程分配秒杀所有可秒杀疫苗')
    parser.add_argument('-pi', '--proxy_ip', action='store_true', help='使用IP代理池 默认不开启该参数')
    parser.add_argument('--log', default='WARNING', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别 默认WARNING')
    return parser.parse_args()


if __name__ == '__main__':
    args = _get_arguments()
    logging.basicConfig(handlers=[logging.FileHandler(filename=LOG_NAME,
                                                      encoding='utf-8', mode='a+')],
                        format='%(asctime)s %(message)s',
                        level=getattr(logging, args.log))
    mm = MiaoMiao(args.tk, args.cookie, args.region_code)
    if args.reload_cache:
        mm.init_data_json()
    run(mm, args.max_workers, args.single_point, args.proxy_ip)
