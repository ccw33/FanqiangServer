# encoding:utf-8
import json
import logging
import pickle
import queue
import threading
import traceback

import requests
import sys

import time
from flask import Flask, render_template, Response, request, send_file, make_response, abort
import mimetypes

from Service.fanqiang_ip_service import fanqiang_service_client, Transformer, db_client
from Utils.conf import Conf
from server_utils import flask_utils

from Service import fanqiang_ip_service
from Utils import log_utils, thread_utils
import server_conf
import cache

app = Flask(__name__, static_folder='static', template_folder='dist')
app.debug = server_conf.is_debug_mode
from Utils.log_utils import logger


# @app.errorhandler(500)
# def error(e):
#     '''
#     错误处理
#     :param e:
#     :return:
#     '''
#     logger.error("%s - %s" % (request.args['uuid'], traceback.format_exc()))
#     return  make_response("服务器出错，请联系管理员，请求id是：%s" % request.args['uuid'], 500)
#
#
# @app.route('/')
# def hello_world():
#     # ip_port=fanqiang_ip_service.get_random_ip_port_dict()
#     # return 'Hello World! ----%s----%s' % (request.args['index'],ip_port)
#     return 'Hello World'
#
#
# @app.route('/get_new_ip_port', methods=['GET'])
# @wrapper_utils.login_checker(request)
# def get_new_ip_port():
#     request_id = request.args['uuid']
#     reason = request.args['reason']
#     try:
#         # 首先测试原来的ip能不能用（防止已更新）
#         # 更新并获取该用户的ip_port(ip_port已失效的情况下才会更新)
#         ip_with_port_1, ip_with_port_2 = user_service.update_and_get_using_ip_port(request.args['account'])
#         return Response(json.dumps([ip_with_port_1, ip_with_port_2]))
#     except Exception as e:
#         # logger.error("%s - %s" % (request_id,traceback.format_exc()))
#         # return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)
#         abort(500)
#
#
# @app.route('/get_delaytime', methods=['GET'])
# def get_delaytime():
#     request_id = request.args['uuid']
#     account = request.args['account']
#     password = request.args['password']
#     try:
#         i = 1 / 0
#         delay = user_service.get_delaytime(account, password)
#         return Response(str(delay))
#     except Exception as e:
#         # logger.error("%s - %s" % (request_id,traceback.format_exc()))
#         # return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)
#         abort(500)


@app.route('/get_pac', methods=['GET', 'POST', 'PUT', 'PATCH'])
# @wrapper_utils.login_checker(request)
def get_pac():
    # request_id = request.args['uuid']
    try:
        pac_type = request.args['type']
        filename, pac = fanqiang_ip_service.get_dynamic_pac(pac_type)

        response = make_response(pac)
        response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename.encode().decode('latin-1'))
        return response
    except Exception as e:
        logger.error("%s" % (traceback.format_exc()))
        # return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)
        abort(500)

@app.route('/get_client_error', methods=['GET'])
def get_client_error():
    '''
    获取有用的ip_port
    :return:
    '''
    try:
        data = request.args.to_dict()
        account = data['account']
        error = data['error']
        logger.error('Client Error : {0}------{1}--------{2}'.format(account,request.environ['REMOTE_ADDR'],error))
        return Response(status=200)
    except Exception:
        logger.error(traceback.format_exc())

@app.route('/get_ip_port', methods=['GET', 'POST', 'PUT', 'PATCH'])
def get_ip_port():
    '''
    获取有用的ip_port
    :return:
    '''
    try:
        data = request.args.to_dict()
        if not (data['account'] == 'CK_test' and data['password'] == 'CK_test'):
            abort(401)
        ip_port_dict = fanqiang_ip_service.get_ip_port_dict_list(1)[0]
        resp = Response(ip_port_dict['ip_with_port'], mimetype='text/plain', status=200)
        return resp
    except Exception:
        logger.error(traceback.format_exc())


def get_ip_port_to_pool():
    '''
    定时获取ip_port到备用池
    :return:
    '''
    try:
        lock = threading.Lock()

        def add_to_useful(ip_port, useful_list):
            try:
                logger.debug('测试ip_port:{0}'.format(ip_port['ip_with_port']))
                is_useful = pickle.loads(fanqiang_service_client.run(
                    Transformer().FanqiangService().test_useful_fanqiang(ip_port).done()).data)
                if is_useful:
                    try:
                        lock.acquire()
                        logger.debug('{0}能用'.format(ip_port['ip_with_port']))
                        useful_list.append(ip_port)
                    finally:
                        lock.release()
            except Exception:
                logger.error(traceback.format_exc())

        # 先读取存下来的pool
        with open('file/bak_pool',
                  'rb') as fr:
            try:
                cache.ip_port_pool = pickle.load(fr)
                logger.debug('从文件读到的数量为：{0}'.format(len(cache.ip_port_pool)))
            except EOFError:
                pass
            except Exception:
                logger.error(traceback.format_exc())

        new_num = int(Conf.get('IP_PORT_POOL', 'new_num'))
        while True:
            useful_list = []
            ## 开20个线程筛掉之前没用的ip_port（由于xmlrpc不支持并发，所以有问题）
            # q = queue.Queue()
            # tf = thread_utils.ThreadFactory()
            # for i in range(20):
            #     t = threading.Thread(target=tf.queue_threads_worker, args=(q, add_to_useful))
            #     t.start()
            # tf.all_task_done = False
            # for ip_port in cache.ip_port_pool:
            #     q.put({'ip_port': ip_port, 'useful_list': useful_list})
            # q.join()
            # tf.all_task_done = True

            for ip_port in cache.ip_port_pool:
                logger.debug('测试ip_port:{0}'.format(ip_port['ip_with_port']))
                is_useful = pickle.loads(fanqiang_service_client.run(
                    Transformer().FanqiangService().test_useful_fanqiang(ip_port).done()).data)
                if is_useful:
                    logger.debug('{0}能用'.format(ip_port['ip_with_port']))
                    useful_list.append(ip_port)

            cache.ip_port_pool = useful_list
            # 如果cache.ip_port_pool不及预期,获取能翻墙的ip_port
            if len(cache.ip_port_pool) < int(Conf.get('IP_PORT_POOL', 'bak_num')):
                new_num += 1
                logger.debug('pool数量{0}达不到要求的{1}'.format(len(cache.ip_port_pool), Conf.get('IP_PORT_POOL', 'bak_num')))
                ip_port_list = pickle.loads(fanqiang_service_client.run(
                    Transformer().FanqiangService().get_useful_fanqiang_ip_port_from_mongo(new_num).done()).data)
                cache.ip_port_pool.extend(ip_port_list)
            else:
                new_num -= 1
            # 把能用的写到文件里面
            with open('file/bak_pool',
                      'wb') as fw:
                try:
                    logger.debug('写到的数量为：{0}'.format(len(cache.ip_port_pool)))
                    pickle.dump(cache.ip_port_pool, fw)
                except EOFError:
                    pass
                except Exception:
                    logger.error(traceback.format_exc())
            # 每分钟检查一次
            time.sleep(60)
    except Exception:
        logger.error(traceback.format_exc())
        logger.error('get_ip_port_to_pool  线程错误关闭')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'doctest':
            import doctest

            doctest.testmod()
    else:
        # 启动线程定时获取有用ip_port
        update_pool_thread = threading.Thread(target=get_ip_port_to_pool)
        update_pool_thread.start()
        # app.debug=True
        app.run(host='0.0.0.0', port='5082',use_reloader=False)
        # app.run(host='0.0.0.0', port='5082',ssl_context='adhoc')
        update_pool_thread.join()
