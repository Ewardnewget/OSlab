#!/usr/bin/python
# -*- coding: UTF-8 -*-

import xmlrpclib,json,os,logging

from flask import Flask,request
from flaskext.xmlrpc import XMLRPCHandler
from logging.handlers import RotatingFileHandler

import tasks

master_server_logger=logging.getLogger('master_server')
master_server_logger.setLevel(level=logging.INFO)
#定义一个RotatingFileHandler，最多备份3个日志文件，每个日志文件最大1K
rHandler = RotatingFileHandler("log.txt",maxBytes = 1*1024*1024,backupCount = 3)
rHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rHandler.setFormatter(formatter)
master_server_logger.addHandler(rHandler)

app = Flask(__name__)
handler = XMLRPCHandler('api')
handler.connect(app, '/RPC2')

slave=[]
slave.append(xmlrpclib.ServerProxy("http://192.168.202.151:10080/",allow_none=True))
slave.append(xmlrpclib.ServerProxy("http://192.168.202.152:10080/",allow_none=True))

def get_greater(slave_resource_list,need):
    if need['memory']>slave_resource_list[0]['Memory'] and need['memory']>slave_resource_list[1]['Memory']:
        return -1
    elif need['memory']>slave_resource_list[0]['Memory']:
        return 1
    elif need['memory']>slave_resource_list[1]['Memory']:
        return 0
    else:
        if slave_resource_list[0]['CPU']<slave_resource_list[1]['CPU']:
            return 0
        else:
            return 1
def schedu():
    master_server_logger.info('new schedu\n')
    tasks.task_queue_lock.acquire()
    slave_resource=[]
    for i in range(len(tasks.Pendinng_queue)):
        task_id = tasks.Pendinng_queue[i]
        with open(tasks.user_data_dir + "/tasks/" + str(task_id)+'/req', "r") as f:
            task = json.load(f)
        task_require_resource = task['resource']
        slave_resource.append(slave[0].get_resource())
        slave_resource.append(slave[1].get_resource())
        greater_resource_salve = get_greater(slave_resource, task_require_resource)
        master_server_logger.info('got greater resource slave number: %d\n',greater_resource_salve)
        if greater_resource_salve != -1:
            master_server_logger.info('starting new task\n')
            slave[greater_resource_salve].new_task(task_id)
            master_server_logger.info('task with id %d starts running\n',task_id)
            tasks.Pendinng_queue.remove(task_id)
            tasks.Running_queue.append(task_id)
            tasks.status_dict[task_id]['slave'] = greater_resource_salve
            tasks.status_dict[task_id]['container']='lxc_'+str(task_id)
            tasks.status_dict[task_id]['status']="Running"
            tasks.status_dict[task_id]['tried_times'] = tasks.status_dict[task_id]['tried_times']+1
            tasks.task_queue_lock.release()
            return json.dumps(tasks.status_dict[task_id])
    tasks.task_queue_lock.release()

def task_failed_handler(task_id):
    tasks.task_queue_lock.acquire()
    tasks.Running_queue.remove(task_id)
    with open('/home/gitdog/Desktop/before','w') as f:
        print >>f,tasks.status_dict[task_id]['maxRetryCount']
    if tasks.status_dict[task_id]['tried_times']<=tasks.status_dict[task_id]['maxRetryCount']:
        tasks.status_dict[task_id]['status']='Pending',
        tasks.Pendinng_queue.append(task_id)
    else:
        tasks.status_dict[task_id]['status']='Failed',
        tasks.Failed_queue.append(task_id)
    tasks.task_queue_lock.release()
    schedu()
    return 'hello'
def task_success_handler(task_id):
    tasks.task_queue_lock.acquire()
    tasks.Running_queue.remove(task_id)
    tasks.status_dict[task_id]["status"] = "Success"
    tasks.Success_queue.append(task_id)
    tasks.task_queue_lock.release()
    schedu()
    return 'hello'
def task_kill_handler(task_id):
    with open('/home/gitdog/Desktop/after','w') as f:
        print>>f,tasks.Pendinng_queue
        print>>f,tasks.Running_queue
        print>>f,tasks.Success_queue
        print>>f,tasks.Failed_queue
    tasks.task_queue_lock.acquire()
    tasks.Failed_queue.remove(task_id)
    tasks.status_dict[task_id]["status"] = "Unknown"
    tasks.Unkown_queue.append(task_id)
    tasks.task_queue_lock.release()
    schedu()
@handler.register
def handle(event_type,task_id):
    if event_type == 'TASK_FAILED':
        task_failed_handler(task_id)
    elif event_type == 'TASK_SUCCESS':
        task_success_handler(task_id)
    elif event_type=='TASK_KILLED':
        task_kill_handler(task_id)
    return 'hello'

def new_task(task):
    tasks.task_queue_lock.acquire()
    tasks.Pendinng_queue.append(task['id'])
    tasks.status_dict[task['id']] = {
        "status": "Pending",
        "tried_times": 0,
        "maxRetryCount":task['maxRetryCount']
    }
    print(tasks.status_dict)
    tasks.task_queue_lock.release()
    schedu()
    return json.dumps(tasks.status_dict[task['id']])
@app.route('/job/task',methods=['POST'])
def submit_task():
    task = request.get_json()
    print(task)
    master_server_logger.info('new task named %s submitted\n',task['name'])

    tasks.task_id_counter_lock.acquire()
    task['id']=tasks.task_id_counter
    try:
        os.mkdir(tasks.user_data_dir+'/tasks/'+str(task['id']))
    except:
        master_server_logger.info('error with make dir %s',tasks.user_data_dir+'/tasks/'+str(task['id']))
    with open(tasks.user_data_dir+'/tasks/'+str(task['id'])+'/req','w') as f:
        json.dump(task,f)
    master_server_logger.info('request file created and stored to glusterfs\n')
    tasks.task_id_counter += 1
    tasks.task_id_counter_lock.release()

    new_task(task)
    suc={
        "code":0,
        "data":{
            "task_id":task['id']
        },
        "message":""
    }
    return json.dumps(suc)

def get_task_status(task_id):
    status=tasks.status_dict[task_id]
    suc={
        'code':0,
        'data':[
            {
                'container_id':status['container'],
                'node_id':'slave'+str(status['slave']),
                'status':status['status']
            }
        ],
        'message':''
    }
    return json.dumps(status)
@app.route("/job/status/<task_id>",methods=["GET"])
def get_status(task_id):
    return get_task_status(int(task_id))

@app.route("/job/kill",methods=["POST"])
def kill_task():
    kill_info=request.get_json()
    slave_num=tasks.status_dict[kill_info['task_id']]['slave']
    return slave[slave_num].kill_task(kill_info['task_id'])

if __name__=="__main__":
    app.run('0.0.0.0',5000)