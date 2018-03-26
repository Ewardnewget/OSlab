## OSLab2

### Part1

rootfs制作流程:

* 创建rootfs文件目录：检测指定的文件目录是否存在，不存在则创建 ; 如果支持brtfs则创建相应的subvolume
* 进行挂载，构建容器arch：如果支持btrfs则对给定的rootfs和配置文件中的rootfs进行合并挂载，并在相应rootfs目录下创建\$cache/rootfs-\$arch的快照，实现容器arch的构建 ; 如果不支持，则直接将$cache/rootfs-\$arch和rootfs进行内容同步，实现容器arch的构建．


### Part2

代码见fakeContainer.c ;

设置CPU只能使用0号，内存上限为512Ｍ，利用stress依次在如下条件下进行压力测试，压力测试结果如下：

* 单进程测试CPU


![c-1](/home/gitdog/git/OSlab/第2次作业/OSlab2-pic/c-1.png)


* 2进程测试CPU



* 5进程测试CPU



* 10进程测试CPU



* 10进程，每进程50Ｍ内存



* 10进程，每进程100Ｍ内存



* 10进程，每进程1.5Ｇ内存


  结果分析 : 可见，在本次lab创建的容器中，基础进程的CPU占用极低，几乎可以忽略，stress进程几乎完全占据了CPU ; 此外，针对内存测试时，发现随着需要的内存增大，实际使用的内存永远不超过512Ｍ，超出部分处理策略为：优先使用系统的swap分区，当swap分区空间也不够时，容器会将相应进程kill．内存超限制时的处理策略可通过cgroup进行设置．memory子系统定义了一个叫mem_cgroup的结构体来管理cgroup相关的内存使用信息，mem_cgroup中包含了两个res_counter成员，分别用于管理memory资源和memory+swap资源，如果memsw_is_minimum为true，则res.limit=memsw.limit，即当进程组使用的内存超过memory的限制时，不能通过swap来缓解。


### Part3

初始进程：lxc的容器初始进程为/sbin/init，/sbin/init 程序会去读取 /etc目录下的 inittab, init.d/rcS 等初始化脚本进行系统的初始化．而此次lab中的容器初始进程为/bin/bash，没有进行系统的初始化操作．

host访问容器：lxc的容器中容器进程可以运行在后台，可通过lxc-attach进入容器进行操作，并且有用户管理的功能．而此次lab中的容器不能在后台运行，不能在保持容器运行的情况下切换出容器，容器生成后可直接执行操作，无用户验证．

资源隔离：lab1通过clone函数的参数设置结合namespace实现了一部分资源的隔离：UTS、IPC、PID、network、NS ; 此外还可以通过cpuset子系统和memory子系统实现对cpu和内存资源的隔离 ; lxc的资源隔离相对而言更加全面和复杂．

网络栈：lab1没有网络栈，不支持对外的网络连接．lxc实现了网络栈，能够完成对外的网络通信.

此外，本次lab没有错误处理方面的功能，没有用户管理的功能．