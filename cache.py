#encoding:utf-8
# 备用ip_port池
import threading

ip_port_pool = []
pool_lock = threading.Lock()