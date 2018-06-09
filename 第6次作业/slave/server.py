#!/usr/bin/python3
import lxc,json,xmlrpc.client
import sys
import os
import threading
from xmlrpc.server import SimpleXMLRPCServer
from resource import get_resource_usage
from SocketServer import ThreadingMixIn
class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):pass

user_data_dir='/home/gitdog/data'

master=xmlrpc.client.ServerProxy('http://192.168.202.151:5000',allow_none=True)

def kill_task(task_id):
    c = lxc.Container('lxc_'+str(task_id))
    if c.state == "STOPPED":
        return {"code": 0, "data": "", "message": ""}  # empty value

    # Try to stop
    c.stop()

    # Check if stop successfully
    if not c.destroy():
        return {"code": 1, "data": "fail", "message": ""}
    else:
        master.handle('TASK_KILLED',task_id)
        return json.dumps({"code": 0, "data": "success", "message": ""})

def run_task_in_container(task):
    task_id = task['id']
    commandLine = task['commandLine']

    code_succ = {"code": 0, "task_id": task_id, "message": "successful!"}
    code_fail = {"code": 1, "task_id": task_id, "message": "failed!"}

    output = open(user_data_dir+'/tasks/'+str(task_id)+'/'+task.get('outputPath', 'output.txt'), 'w+')
    log_file=open(user_data_dir+'/tasks/'+str(task_id)+'/log', 'w+')
    c = lxc.Container('lxc_'+str(task_id))

    if not c.defined:
        # Create the container rootfs
        lxc_choice = {"dist": "debian", "release": "sid", "arch": "amd64"}
        if not c.create("download", lxc.LXC_CREATE_QUIET, lxc_choice):
            print("Failed to create the container rootfs", file=log_file)
            master.handle('TASK_FAILED',task_id)
            return

    print("defined the container", file=log_file)

    # # Load the image
    # image = task.get('imageId', None)
    # if image is not None:
    #     rootfs_path = '/var/lib/lxc/%s/rootfs' % image
    #     c.set_config_item('lxc.rootfs', rootfs_path)
    # else:
    #     rootfs_path = '/var/lib/lxc/debian/rootfs'
    #     c.set_config_item('lxc.rootfs', rootfs_path)
    # print("loaded the image", file=log_file)

    # Limit the resource
    resource = task.get('resource', None)
    if resource is not None:
        #if 'cpu' in resource:
        #    c.set_config_item('lxc.cgroup.cpuset.cpus', str(resource.get('cpu')))
        if 'memeory' in resource:
            c.set_config_item('lxc.cgroup.memory.limit_in_bytes', str(resource.get('memory')))
    print("limited the resource", file=log_file)
    # Mount the package path
    package_path = user_data_dir+task.get('packagePath', None)
    if package_path is not None:
        c.set_config_item('lxc.mount.entry', '%s home none bind,rw,create=dir 0 0' % package_path)
    print("mounted the pakage_path", file=log_file)
    # Start the container
    if not c.start():
        master.handle('TASK_FAILED', task_id)
        return

    print("started the container", file=log_file)

    success_flag = False

    # Wait for connectivity
    if not c.get_ips(timeout=5):
        master.handle('TASK_FAILED', task_id)
    else:
        exit_code = c.attach_wait(lxc.attach_run_command, ["bash", "-c", commandLine], stdout=output,
                                      stderr=log_file)
        if exit_code == 0:
            success_flag = True
        # Check if it's succeeded
        if not success_flag:
            master.handle('TASK_FAILED', task_id)
            print("Failed to run the task", file=log_file)
        else:
            master.handle('TASK_SUCCESS',task_id)
    # Shutdown the container
    if not c.shutdown(5):
        c.stop()
        if not c.stop():
            print("Failed to kill the container", file=log_file)
    if not c.destroy():
        print("Failed to destroy the container.", file=log_file)
    return 'hello'


def new_task(task_id):
    with open(user_data_dir + "/tasks/" + str(task_id)+'/req', "r") as f:
        task=json.load(f)
    threading.Thread(target=run_task_in_container, args=[task]).start()
    threading.Timer(task['timeout'], kill_task, args=[task_id]).start()
    return 'hello'

def get_resource():
    resource_usage = get_resource_usage()
    print(resource_usage)
    resource_state = {
        "CPU": resource_usage['cpu']['cpuUsed'],
        "Memory": resource_usage['memory']['memTotal'] - resource_usage['memory']['memUsed']
    }
    return resource_state

if __name__ == '__main__':
    # Create server
    server = ThreadXMLRPCServer(('0.0.0.0', 10080))
    server.register_function(new_task)
    server.register_function(kill_task)
    server.register_function(get_resource)
    server.serve_forever()