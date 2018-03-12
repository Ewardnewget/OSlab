### 1.了解虚拟机和容器技术，用自己的话简单叙述、总结并对比

#### 虚拟机

* 虚拟机是在Hypervisor的基础上建立起来的，Hypervisor是运行在物理主机与Guest OS之间的中间软件层，允许多个操作系统及其应用共享一套基础物理资源，它可以协调访问服务器上的所有物理设备和虚拟机．Hypervisor分为两种：裸机型和宿主机型．裸机型直接运行在物理主机上，是一种基于内核的虚拟机，具有资源开销小 高可用性 高可靠性 和优秀的可拓展性等优点．宿主机型运行在宿主机器的操作系统上，进行硬件的全仿真，相对而言成本较低．
* 在Hypervisor的基础上，虚拟机的整体结构图由上到下依次为：应用程序 Guest OS Hypervisor Host OS 硬件基础设施．在Hypervisor基础上可以允许多个Guest OS同时存在，他们之间互不干扰．

#### 容器

* 容器是一种内核级的虚拟化解决方案，它通过在Host OS之上添加一层管理层实现对容器的隔离．
* 它在内核的基础上通过namespace对各个容器下的进程和资源进行隔离，PID,IPC,Network等系统资源不再是全局性的，而是属于特定的Namespace。每个Namespace里面的资源对其他Namespace都是透明的。各个容器之间的操作无法互相影响．
* Cgroups可以实现对单个进程或多个进程的资源的精细限制，容器技术利用Cgroups对各个容器的CPU内存等资源进行限制，避免资源的独占等问题．
* 容器技术还通过rootfs提供对虚拟文件系统的支持．

#### 对比

* 虚拟机是系统层面上的虚拟化技术，各个虚拟机内部包含Guest OS 库文件 应用程序，允许多个不同的系统环境并存，各个虚拟机之间完全独立．容器是进程层面上的虚拟化技术，同一主机上的各个容器必须运行在同样的系统环境中，容器内部只包含库文件和应用程序，每个容器都共享主机操作系统的内核，通常还包括文件的库．因此容器相对虚拟机而言资源消耗更小，更突出＂轻量级＂和启动快速等特点，但由于共享Host OS的内核，容器的独立性比虚拟机更弱一些．

### 2. 利用[LXC Python API](https://linuxcontainers.org/lxc/documentation/)编写程序，要求执行该程序会先创建并启动一个Debain系统容器，然后该程序会在容器根目录创建一个名为 Hello-Container的文件，并在文件中写入姓名和学号.

代码如下，也可在文件testlxc.py中查看

```python
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import lxc

c=lxc.Container("testlxc")

if c.defined:
    print("Container already exists")
    exit(1)

#create the container rootfs
if not c.create(template="debian"):
    print("Fail to create the container rootfs")
    exit(1)

#start the container
if not c.start():
    print("Fail to start the container")
    exit(1)

#create file
c.attach_wait(lxc.attach_run_command,["touch","Hello-Container"])
c.attach_wait(lxc.attach_run_command,["bash","-c",'echo "姓名：祝世豪\n学号：1500012848" >Hello-Container'])

#stop the container
if not c.shutdown(5):
    c.stop()
```




