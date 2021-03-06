#encoding:utf-8
import logging
import math
import pickle
import random
import re
from functools import reduce

import requests
import cache
from Utils import log_utils
from Utils.log_utils import logger


# from model import ip,user as user_model
# fanqiang = ip.Fanqiang()
# user = user_model.User()

# def get_random_useful_ip_port_dict()->dict:
#     '''
#     获取一个有用的ip_port_dict
#     :return:
#     '''
#     ip_list = list(fanqiang.query())
#     if not ip_list:
#         raise Exception('没有可用ip')
#     ip_port_dict = ip_list[math.floor(random.random() * len(ip_list))]
#     try:
#         use_time = test_proxy(ip_port_dict)
#         ip_port_dict["time"] = use_time
#         return ip_port_dict
#     except (scribe_utils.RobotException,\
#            requests.exceptions.ConnectionError, requests.ReadTimeout, requests.exceptions.SSLError) as e: # request 访问错误
#         disable_and_update_if_needed(ip_port_dict)
#         logger.debug('随机ip_port %s 无法翻墙，从新获取' % ip_port_dict['ip_with_port'])
#         return get_random_useful_ip_port_dict()
#
#
# def test_proxy(ip_port_dict):
#     '''
#     测试ip代理
#     :param ip_port_dict: 包含ip port等数据的dict对象
#     :type ip_port_dict: dict
#     :return:use_time 用时，秒为单位。
#     '''
#     ip_with_port = ip_port_dict['ip_with_port']
#     proxy_type = ip_port_dict['proxy_type']
#     logger.debug('开始测试%s' % ip_with_port)
#     resp = requests.get('https://www.baidu.com/', headers=scribe_utils.headers,
#                         proxies={'http': proxy_type + (
#                             'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port,
#                                  'https': proxy_type + (
#                                      'h' if proxy_type == 'socks5' else '') + '://' + ip_with_port},
#                         timeout=10)
#     use_time = resp.elapsed.microseconds / math.pow(10, 6)
#     return use_time
#
# def disable_times_add_one(ip_port_dict):
#     '''
#     更新disable_times（加1）
#     :param ip_port_dict:
#     :return:
#     '''
#     new_disable_times = ip_port_dict['disable_times'] + 1
#     fanqiang.update({'disable_times': new_disable_times}, {'_id': ip_port_dict['_id']})
#     def is_disable_times_lg_10():
#         '''
#         判断代理失效次数是否大于10，是返回True
#         :param ip_port_dict:
#         :return:
#         '''
#         return ip_port_dict['disable_times'] > 10
#
#     return is_disable_times_lg_10
#
#
# def delete_and_update_ip_port(ip_with_port)->str:
#     '''
#     删除ip_port_dict 同时级联更新使用该ip_port的用户的ip_with_port字段
#     :param ip_with_port:
#     :type ip_with_port:str
#     :return:
#     '''
#     fanqiang.delete({'ip_with_port':ip_with_port})
#     new_ip_with_port = get_random_useful_ip_port_dict()['ip_with_port']
#     user.update({'ip_with_port_1':new_ip_with_port},{'ip_with_port_1':ip_with_port})
#     user.update({'ip_with_port_2':new_ip_with_port},{'ip_with_port_2':ip_with_port})
#     return new_ip_with_port
#
#
# def disable_and_update_if_needed(ip_port_dict)->str:
#     '''
#     ip_port_dict的disable_times字段加1，同时如果超过10就更新相关的ip_port_dict和user数据并返回更新后的ip_with_port。
#     否组返回原来的ip_with_port
#     :param ip_port_dict:
#     :return:
#     '''
#     is_disable_totaly = disable_times_add_one(ip_port_dict)
#     if is_disable_totaly():
#         return delete_and_update_ip_port(ip_port_dict['ip_with_port'])
#     return ip_port_dict['ip_with_port']

from RPC import RPC_Client
Transformer = RPC_Client.Transformer
db_client = RPC_Client.MyServerProxy(RPC_Client.SERVERS_FOR_CLIENT.FanqiangService)
fanqiang_service_client = RPC_Client.MyServerProxy(RPC_Client.SERVERS_FOR_CLIENT.FanqiangService)


# def get_dynamic_pac(pac_type,account)->(str,str):
#     '''
#     动态生成pac文件提供用户下载
#     :param pac_type: 有surge,auto_switch，socks3种，后面两个用于chrome
#     :param account: 账号，用于获取用户所使用的ip_with_port
#     :return:
#     '''
#     filename=''
#     pac=''
#
#     def get_ip_port_dict_list(account)->list:
#         '''
#         获取用户所使用的ip_with_port_list
#         :param account:
#         :return:
#         '''
#         u = db_client.run(Transformer().user.query({'account': account}).next().done())
#         # u = user.query({'account': account}).next()
#         ip_port_dict_list = []
#         if u['ip_with_port_1']:
#             ip_port_dict_list.append(db_client.run(Transformer().ip.Fanqiang().query({'ip_with_port': u['ip_with_port_1']}).next().done()))
#         if u['ip_with_port_2']:
#             ip_port_dict_list.append(db_client.run(Transformer().ip.Fanqiang().query({'ip_with_port': u['ip_with_port_2']}).next().done()))
#
#         return ip_port_dict_list
#
#     def generate_replace_text(ip_fanqiang_list):
#         '''
#         根据ip_fanqiang_list生成替换文字
#         :param ip_fanqiang_list:
#         :return:
#         '''
#         new_proxy_list = ["%s%s = %s,%s\n" % (
#             ip['proxy_type']+'_', str(index), ip['proxy_type'] if ip['proxy_type'] == 'http' else 'socks5',
#             ip['ip_with_port'].replace(':', ',')) for index, ip in enumerate(ip_fanqiang_list)]
#         new_proxy_group = [s.split('=')[0] for s in new_proxy_list]
#         return (reduce(lambda v1, v2: v1 + v2, new_proxy_list), reduce(lambda v1, v2: v1 + ',' + v2, new_proxy_group) + ',')
#
#     def get_dynamic_chrome_file(filename):
#         # 替换ip和port
#         ip_port_dict_list = get_ip_port_dict_list(account)
#         ip_with_port = ip_port_dict_list[0]['ip_with_port']
#         with open('file/pac/'+filename,
#                   'r', encoding='utf-8') as fr:
#             old_text = fr.read()
#             new_text = old_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[0],
#                                         ip_with_port)
#             new_text = new_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[1],
#                                         ip_with_port)
#             return new_text
#
#     if pac_type=='surge':
#         filename = 'http_surge.pac'
#         ip_port_dict_list=get_ip_port_dict_list(account)
#
#         with open('file/pac/'+filename, 'r', encoding='utf-8') as fr:
#             old_text = fr.read()
#             proxy_replace_text, group_replace_text = generate_replace_text(ip_port_dict_list)
#             new_text = old_text.replace(re.findall(r'\[Proxy\]\n((?:.+\n)+)Socks1',
#                                                    old_text)[0], proxy_replace_text)
#             new_text = new_text.replace(
#                 re.findall(
#                     r'\[Proxy Group\]\nProxy = url-test, (.+) url = http://www.google.com/generate_204\nSocks_Proxy',
#                     new_text)[0], group_replace_text)
#             pac = new_text
#     if pac_type == 'socks':
#         filename = 'OmegaProfile_socks.pac'
#         pac = get_dynamic_chrome_file(filename)
#     if pac_type == 'auto_switch':
#         filename = 'OmegaProfile_auto_switch.pac'
#         pac = get_dynamic_chrome_file(filename)
#     if filename and pac:
#         return filename,pac
#     else:
#         raise Exception('获取动态pac失败，{}获取了空值'.format('filename' if not filename else 'pac'))


def get_ip_port_dict_list(n) -> list:
    '''
    获取n个有效的ip_port_dict_list
    :param n: 获取的数量
    :return:
    '''
    # u = db_client.run(Transformer().user.query({'account': account}).next().done())
    # # u = user.query({'account': account}).next()
    # ip_port_dict_list = []
    # if u['ip_with_port_1']:
    #     ip_port_dict_list.append(db_client.run(Transformer().ip.Fanqiang().query({'ip_with_port': u['ip_with_port_1']}).next().done()))
    # if u['ip_with_port_2']:
    #     ip_port_dict_list.append(db_client.run(Transformer().ip.Fanqiang().query({'ip_with_port': u['ip_with_port_2']}).next().done()))
    ip_port_dict_list = []
    if n >= len(cache.ip_port_pool):
        return cache.ip_port_pool
    try:
        cache.pool_lock.acquire()
        while len(ip_port_dict_list) < n:
            ip_port = cache.ip_port_pool[math.floor(random.random() * len(cache.ip_port_pool))]
            if ip_port not in ip_port_dict_list:
                ip_port_dict_list.append(ip_port)
    finally:
        cache.pool_lock.release()
    return ip_port_dict_list

def get_dynamic_pac(pac_type)->(str,str):
    '''
    动态生成pac文件提供用户下载
    :param pac_type: 有surge,auto_switch，socks3种，后面两个用于chrome
    :return:
    '''
    filename=''
    pac=''

    def generate_replace_text(ip_fanqiang_list):
        '''
        根据ip_fanqiang_list生成替换文字
        :param ip_fanqiang_list:
        :return:
        '''
        new_proxy_list = ["%s%s = %s,%s\n" % (
            ip['proxy_type']+'_', str(index), ip['proxy_type'] if ip['proxy_type'] == 'http' else 'socks5',
            ip['ip_with_port'].replace(':', ',')) for index, ip in enumerate(ip_fanqiang_list)]
        new_proxy_group = [s.split('=')[0] for s in new_proxy_list]
        return (reduce(lambda v1, v2: v1 + v2, new_proxy_list), reduce(lambda v1, v2: v1 + ',' + v2, new_proxy_group) + ',')

    def get_dynamic_chrome_file(filename):
        # 替换ip和port
        ip_port_dict_list = get_ip_port_dict_list(1)
        ip_with_port = ip_port_dict_list[0]['ip_with_port']
        with open('file/pac/'+filename,
                  'r', encoding='utf-8') as fr:
            old_text = fr.read()
            new_text = old_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[0],
                                        ip_with_port)
            new_text = new_text.replace(re.findall(r'(?:SOCKS |SOCKS5 )(\d+\.\d+\.\d+\.\d+:\d+)', old_text)[1],
                                        ip_with_port)
            return new_text

    if pac_type=='surge':
        filename = 'http_surge.pac'
        ip_port_dict_list=get_ip_port_dict_list(5)

        with open('file/pac/'+filename, 'r', encoding='utf-8') as fr:
            old_text = fr.read()
            proxy_replace_text, group_replace_text = generate_replace_text(ip_port_dict_list)
            new_text = old_text.replace(re.findall(r'\[Proxy\]\n((?:.+\n)+)Socks1',
                                                   old_text)[0], proxy_replace_text)
            new_text = new_text.replace(
                re.findall(
                    r'\[Proxy Group\]\nProxy = url-test, (.+) url = http://www.google.com/generate_204\nSocks_Proxy',
                    new_text)[0], group_replace_text)
            pac = new_text
    if pac_type == 'socks':
        filename = 'OmegaProfile_socks.pac'
        pac = get_dynamic_chrome_file(filename)
    if pac_type == 'auto_switch':
        filename = 'OmegaProfile_auto_switch.pac'
        pac = get_dynamic_chrome_file(filename)
    if filename and pac:
        return filename,pac
    else:
        raise Exception('获取动态pac失败，{}获取了空值'.format('filename' if not filename else 'pac'))