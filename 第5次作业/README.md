### 第5次作业

#### PART1

场景：[日志复制](http://www.jdon.com/artichect/raft.html)

raft采用半数选举机制确定Leader，任意时刻任一节点可以扮演以下角色：

1. Leader: 处理所有客户端交互，日志复制等，一般一次只有一个Leader.
2. Fllower
3. Candidate：候选者，可申请参选Leader

Raft阶段分为两个，首先是选举过程，然后在选举出来的领导人带领进行正常操作。

选举过程：

Raft 算法将时间划分成为任意不同长度的任期（term）。任期用连续的数字进行表示。每一个任期的开始都是一次选举（election）。Leader通过向Fllower发送心跳信息保证自己的领导人地位，每个Fllower有一个时钟，若在时钟周期内未收到Leader发送的心跳信息，则变为Candidate，自增当前任期，参与竞选，向其他节点发送投票请求，一个候选人会一直处于该状态，直到下列三种情形之一发生：

- 它赢得了选举；
- 另一台服务器赢得了选举；
- 一段时间后没有任何一台服务器赢得了选举

投票节点根据任期号等信息决定是否投票。

选举结束后，Leader接收客户端请求，每一个客户端请求都包含一条需要被复制状态机（replicated state machine）执行的命令。领导人把这条命令作为新的日志条目加入到它的日志中去，然后并行的向其他服务器发起 AppendEntries RPC ，要求其它服务器复制这个条目。当这个条目被安全的复制之后（下面的部分会详细阐述），领导人会将这个条目应用到它的状态机中并且会向客户端返回执行结果。Fllower根据任期号等信息确定是否添加该日志。

#### PART2

##### GlusterFS

GlusterFS是一种Scale-Out的去中心化的分布式存储解决方案，具有强大的横向扩展能力，通过扩展能够支持数PB存储容量和处理数千客户端。GlusterFS借助TCP/IP或InfiniBand RDMA网络将物理分布的存储资源聚集在一起，使用单一全局命名空间来管理数据。GlusterFS基于可堆叠的用户空间设计，可为各种不同的数据负载提供优异的性能。GlusterFS支持运行在任何标准IP网络上标准应用程序的标准客户端，用户可以通过NFS/CIFS等标准协议或GlusterFS client访问文件系统。

整体架构如下：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/Gluster_arch.png)

GlusterFS具有以下特点：

1. 扩展性和高性能：scale-out架构允许通过简单地增加资源来提高存储容量和性能，利用弹性哈希算法消除了元数据的需求，解决了单点性能瓶颈，实现了真正的并行化。
2. 高可用性：自带容错机制，可以对文件进行自动复制，如镜像或多次复制，包含错误恢复机制。
3. 全局统一命名空间：全局统一命名空间将磁盘和内存资源聚集成一个单一的虚拟存储池，对上层用户和应用屏蔽了底层的物理硬件。
4. 弹性卷管理：数据储存在逻辑卷中，逻辑卷可以从虚拟化的物理存储池进行独立逻辑划分而得到。存储服务器可以在线进行增加和移除，不会导致应用中断。
5. 线性横向扩展：利用改进的hash算法实现了线性的横向扩展能力。
6. 高可靠性

使用方法：

![Gluster_work](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/Gluster_work.png)

1. 用户通过glusterfs的mount point 来读写数据，用户请求被递交给本地VFS处理，VFS将数据递交给FUSE内核文件系统，FUSE将数据转交给client
2. client对数据进行一系列处理，利用hash算法计算出目标文件所在服务器，并向该服务器发送请求。
3. 服务器完成操作后返回数据

构建好GlusterFS后，用户只需要将共享文件系统挂在到本地，利用cient即可访问。

##### AUFS

AUFS是一种Union File System，即将不同物理位置的目录合并mount到同一个目录中。类似于层级结构，高层共享低层的文件，每层具有不同的权限，可以通过mount进行设置，一般低层文件为read-only，高层为ro+wh，对于共享文件的写操作，采用增量存储形式，类似于copy-on-write。AUFS可用来实现文件系统的复用，降低重复性文件的存储需求，减少存储空间要求。

![AUFS](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/AUFS.png)

使用方式：将共享文件进行挂载即可，挂载时设置好访问权限：

```
mount -t aufs -o dirs=./Branch-0:./Branch-1:./Branch-2 none ./MountPoint
```

还可以进行对应的卸载：

```
umount MountPoint
```

#### PART3

host: OSlab1和OSlab2

```shell
# on both hosts
# edit /etc/hosts as:
127.0.0.1	localhost	OSlab2
192.168.202.156	OSlab2	gluster2
192.168.202.151	OSlab1	gluster1
```

```shell
# on host1(任意一边都可以，此处选用host1)
sudo gluster peer probe OSlab2
sudo gluster volume create gvol0 replica 2 OSlab1:/home/gitdog/gvol0 OSlab2:/home/gitdog/gvol0 force
sudo gluster volume start gvol0
sudo gluster volume info gvol0
```

![gluster_info](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/gluster_info.png)

```shell
# in container c
# edit /etc/hosts
127.0.0.1	localhost	OSlab2
192.168.202.156	OSlab2	gluster2
192.168.202.151	OSlab1	gluster1

mkdir data
sudo apt install attr
sudo mknod /dev/fuse c 10 229
sudo mount -t glusterfs OSlab1:/home/gitdog/gvol0 /data/
```

![lxc_gluster](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/lxc_gluster.png)

![host_gluster](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/host_gluster.png)

#### PART4

```shell
# on host1
mkdir /var/lib/lxc/aufs_c2
mkdir /var/lib/lxc/aufs_c2/rootfs
cp /var/lib/lxc/c/config /var/lib/lxc/aufs_c2/config
# 修改config
lxc.utsname = aufs_c2
lxc.rootfs = /var/lib/lxc/aufs_c2/rootfs
# 挂载
mount -t aufs -o dirs=/var/lib/lxc/c/rootfs/=ro none /var/lib/lxc/aufs_c2/rootfs
```

此时，aufs_c2为只读状态：

![aufs0](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/aufs0.png)

![aufs1](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/aufs1.png)

```shell
umount /var/lib/lxc/aufs_c2/rootfs
mkdir /var/lib/lxc/aufs_c2/aufs_c2_write
mount -t aufs -o dirs=/var/lib/lxc/aufs_c2/aufs_c2_write/=rw:/var/lib/lxc/c/rootfs/=ro none /var/lib/lxc/aufs_c2/rootfs
```

此时，可写：

![aufs2](https://github.com/Ewardnewget/OSlab/raw/master/第5次作业/pic/aufs2.png)

#### 参考

[GlusterFS on ubuntu](https://www.itzgeek.com/how-tos/linux/ubuntu-how-tos/install-and-configure-glusterfs-on-ubuntu-16-04-debian-8.html)

[mount GlusterFS to lxc](https://www.cyberciti.biz/faq/how-to-mount-glusterfs-volumes-inside-lxclxd-linux-containers/)

