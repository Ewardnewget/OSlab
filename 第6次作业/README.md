### 第六次作业



#### 运行

master:

```python
# in /master
sudo python server.py
```

slave:

```python
# in /slave
sudo python3 server.py
```



#### 系统设计

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/arch.png)

task请求文件、镜像、输入文件、输出文件等存储在glusterfs中。

受到新任务请求后，首先将新任务加入pending队列，并调用scheduler（）进行任务调度。任务被分配到资源利用率较低的节点（本实验中简单获取了节点资源状况，并选择剩余内存较多的节点）：master调用rpc将task_id发送到slave，slave启动新线程作为monitor，monitor进行容器的启动和任务的执行，当任务成功（或失败退出）时，slave调用rpc向master发送event，master根据event进行状态转换。

失败的任务若还有重试次数，会在master收到event并处理后重新进入pending，等待重新调度。

新任务以及任务失败或者成功等会导致资源释放的时间会触发scheduler的执行。

#### 测试

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/echo.PNG)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/psef.PNG)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/echo_success.PNG)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/psef_running.PNG)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/echo_result.png)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/ps_result.png)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/error.PNG)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第6次作业/pic/error_failed.PNG)

#### 问题和改进点

由于SimpleXMLRPC本身的问题，rpc不能支撑多线程安全通信，有时会导致rpc请求发送失败。

此处采用python的lxc库进行lxc的全部相关工作，没能使用aufs节省空间。可以结合shell脚本和lxc库实现aufs的使用。

```python
    if not os.path.exists('/var/lib/lxc/lxc_'+str(task_id)):
        os.system('mkdir /var/lib/lxc/lxc_'+str(task_id))
    if not os.path.exists('/var/lib/lxc/lxc_'+str(task_id)+'/rootfs'):
        os.system('mkdir /var/lib/lxc/lxc_' + str(task_id)+'/rootfs')
    if not os.path.exists('/var/lib/lxc/lxc_'+str(task_id)+'/config'):
        os.system('touch /var/lib/lxc/lxc_'+str(task_id)+'/config')
    print("hello")
    with open('/var/lib/lxc/ubuntu16.04/config','r') as f:
        lines=f.readlines()
    with open('/var/lib/lxc/lxc_'+str(task_id)+'/config','w') as f:
        line_num=0
        for line in lines:
            if line_num==16:
                f.write('lxc.utsname = lxc_'+str(task_id)+'\n')
            elif line_num==14:
                f.write('lxc.rootfs = /var/lib/lxc/lxc_'+str(task_id)+'/rootfs\n')
            else:
                f.write(line)
            line_num+=1
        f.write('lxc.mount.entry = /home/gitdog/lab_nfs home/ubuntu/data none bind,rw,create=dir 0 0')
    if not os.path.exists('/var/lib/lxc/lxc_'+str(task_id)+'/writeable'):
        os.system('mkdir /var/lib/lxc/lxc_'+str(task_id)+'/writeable')
    os.system('mount -t aufs -o dirs=/var/lib/lxc/lxc_'+str(task_id)+'/writeable/=rw:/var/lib/lxc/ubuntu16.04/rootfs/=ro none /var/lib/lxc/lxc_'+str(task_id)+'/rootfs')
```

