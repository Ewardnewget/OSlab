## 第四次作业

#### PartA 叙述以下三种情况下容器通信的网络处理过程

##### 同一host上同一子网内的两容器

一个容器发送数据包，将ARP包广播给同一子网内的各个端口，找到目标地址对应的的端口后发送数据包，不经过网关。

##### 同一host上不同子网内的两容器

网关不相通的情况下, 包在走出容器时到达网桥，会加上tag, 因为tag不同, 不能进入另一个容器对应的port, 所以不相通

##### 通过gre隧道相连的两个host上同一子网内的两容器

包在走出容器到达网桥时，加上tag, 经过gre隧道时，加上remote_ip封装,并从网卡发送到另一台host, 网卡, gre分别解掉对应的包头, 之后的包进入具有同样tag的port, 找到另一个容器

#### PartB 了解并叙述vlan技术的原理，解释vlan在用户隔离数量上的限制

原理：  

同一交换机的所有端口都在同一广播域，任意一个端口能够接收到其他所有端口发送的广播报文，不利于网络的隔离。

vlan，即虚拟局域网，遵循IEEE802.1Q协议，可以通过不同的方式将局域网内的网络设备从逻辑上划分为不同的虚拟局域网，每个虚拟局域网功能与现实的局域网类似，每个端口发送的广播报文只会发送到同一vlan的其他端口，可以理解为以软件的方法构建了虚拟的switches，为Ethernet提供更加灵活地控制手段。  

vlan有多种划分方法：基于端口、基于MAC、基于IP网段、基于协议以及基于策略（以上多种的结合）的划分方式。

vlan有三种端口类型：Access（一般用于连接主机）、Trunk（只能连接switch和route）、Hybird（混合）

在数据帧中有四个字节为802.1Q的VLAN Tag，其中，Tag Protocol ID占据两个字节，包含一个固定值0x8100，表示这是一个802.1Q标签的帧。Tag Control Information占据剩余两个字节，存储控制信息，VLAN ID占据其中的12个bit，因此vlan上限为4096，但其中0和4095用作协议保留，因此vlan实际上限为4094，当用户隔离域的数量超过4094时，vlan不再适用。

#### PartC 调研vxlan技术，比较其与gre技术的差异

vxlan，即可扩展虚拟局域网，随着大规模计算集群的发展，普通的vlan不能满足管理上的需求，vxlan应运而生，它解决了一系列问题：L2网络的规模问题、动态网络调整和隔离、虚拟机迁移等。

网络结构如下：


 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/vxlan网络结构.png)


NVE(Network Virtrualization Edge网络虚拟边缘节点）是实现网络虚拟化的功能实体，报文经过NVE封装后，NVE之间就可以在基于L3的网络基础上建立起L2虚拟网络。网络设备实体以及服务器实体上的VSwitch都可以作为NVE。

VTEP为VXLAN隧道的端点，封装在NVE中，用于VXLAN报文的封装和解封装。VTEP与物理网络相连，分配的地址为物理网络IP地址。VXLAN报文中源IP地址为本节点的VTEP地址，VXLAN报文中目的IP地址为对端节点的VTEP地址，一对VTEP地址就对应着一个VXLAN隧道。

vxlan采用MAC in DUP的技术，用三层协议封装二层协议，

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/vxlan-2.png)

vxlan header：共计8bytes，其中24bits为VNI（Vxlan Netword identifier），类似VLAN ID，用于区分VXLAN段，不同VXLAN段的虚拟机不能直接二层相互通信。

外层UDP Header：目的端口使用4798，但是可以根据需要进行修改。

Outer IP Header：源IP为发送报文的设备所属的VTEP的IP地址，目的IP为目的设备所属的VTEP的IP地址。

Outer Mac Header：源地址为发送报文的设备所属的VTEP MAC地址，目的地址为目的设备所属的VTEP上路由表中下一跳MAC地址。

通信模式主要有3种：同VNI下的不同设备（分布在同一实体和不同实体两种），不同VNI下的跨网访问，VXLAN和非VXLAN之间的访问。

VXLAN网关分为：

二层网关：位于同一网段的终端用户通信，根据Mac地址进行报文转发

三层网关：用于非同一网段的终端用户通信或VXLAN和非VXLAN用户间的通信

##### 比较

GRE和VXLAN都是用于封装其它协议的，都用三层协议封装二层协议，这两项技术都解决了VLAN规模固定的问题，不再局限于4094个。区别在于：

1)  GRE是一种通用的封装格式，而VXLAN主要用于封装、转发2层报文。GRE的通用性更好，但从功能上说，vxlan要更加优秀。

2）GRE通过路由器进行协议的封装和解封，而vxlan有专有的封装和解封的组件：VTEP。相对应的，包的传播过程就有一定差别，在GRE中，由于路由器两段的地址都是配置好的，因此报文转发不存在地址的学习过程；而在vxlan中，源设备并不知道目的设备的VTEP，因此需要先进行组播学习，即报文会发给所有同在这个网络组中的其他VTEP，若目的VTEP已经通过学习获知，则不需要组播过程。VXLAN避免了GRE的点对点必须有连接的缺点。

3） VXLAN 使用 UDP 封包格式，GRE 采用一般路由封装（Generic Routing Encapsulation，GRE）格式。GRE 封包格式由 GRE 表头来包裹被封装的第二层封包，但是和 VXLAN 不同，內部的第二层封包不支持 802.1Q ，此因此可能对虚拟网络上层应用产生限制。

4）GRE不能兼容传统负载均衡

5）VXLAN数据包比较大，需要借助支持大型帧的传输网络才能支持数据包规模的扩展

6）GRE支持减小数据包最大传输单元以减小内部虚拟网络数据包大小，不需要要求传输网络支持传输大型帧。

#### PartD

##### 基于ovs，通过vlan和gre技术构建两个隔离的lxc容器集群

在192.168.202.152和192.168.202.151两台虚拟机上进行实验：

```shell
#192.168.202.151上
#添加ovs网桥
 sudo ovs-vsctl add-br ovs-br
 sudo ip link set ovs-br up
#添加port并设置地址作为lxc的gateway
 sudo ovs-vsctl add-port ovs-br port1 -- set interface port1 type=internal
 sudo ovs-vsctl add-port ovs-br port2 -- set interface port2 type=internal
 sudo ip addr add 172.16.1.1/24 dev port1
 sudo ip addr add 172.16.2.1/24 dev port2
 sudo ip link set port1 up
 sudo ip link set port2 up
#设置port的tag标记不同虚拟局域网
 sudo ovs-vsctl set port port1 tag=101
 sudo ovs-vsctl set port port2 tag=202
#添加远程端口，连接192.168.202.152
 sudo ovs-vsctl add-port ovs-br gre_152 -- set interface gre_152 type=gre options:remote_ip=192.168.202.152
#设置转发规则
 sudo iptables -t nat -A POSTROUTING -s 172.16.1.0/24 -j MASQUERADE
 sudo iptables -t nat -A POSTROUTING -s 172.16.2.0/24 -j MASQUERADE

```
网桥结构：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/ovs-br-show.png)

容器设置如下：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c1_config.png)

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c2_config.png)

```shell
#192.168.202.152上
#添加ovs网桥
 sudo ovs-vsctl add-br ovs-br
 sudo ip link set ovs-br up
#添加port并设置地址作为lxc的gateway，添加tag作为虚拟局域网1的标识
 sudo ovs-vsctl add-port ovs-br port3 -- set interface port3 type=internal
 sudo ip addr add 172.16.1.1/24 dev port3
 sudo ip link set port3 up
 sudo ovs-vsctl set port port3 tag=101
#添加远程端口，连接192.168.202.151
 sudo ovs-vsctl add-port ovs-br gre_151 -- set interface gre_151 type=gre option:remote_ip=192.168.202.151
```
网桥结构：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/ovs-br-show2.png)

容器设置如下：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c3_config.png)

实验结果如下：

c1 ping c3（同一子网，不同host）：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c1_ping_c3.png)

c2 ping c3 （不同子网，不同host）:

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c2_ping_c3.png)

c2 ping c1 （同一host，不同子网）：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c2_ping_c1.png)

c3 ping c1（同一子网，不同host）：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c3_ping_c1.png)

c3 ping c2 （不同子网，不同host） ：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/c3_ping_c2.png)

##### 使用ovs对容器集群的网络进行流量控制，对每个容器集群出口上行下行流量进行限速并测评

利用ovs的Qos功能实现流量限制，利用netperf工具测试。

在192.168.202.152上运行netserver，在容器c1内通过netperf进行测试。

**ingress_policing_rate：**为接口最大收包速率，单位kbps，超过该速度的报文将被丢弃，默认值为0表示关闭该功能；
**ingress_policing_burst：**为最大突发流量大小，单位kb。默认值0表示1000kb，这个参数最小值应不小于接口的MTU，通常设置为ingress_policing_rate的10%更有利于tcp实现全速率；

限制前：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/before_qos.png)

```shell
#带宽上限为1mb
# ovs-vsctl set interface port1 ingress_policing_rate=1000
# ovs-vsctl set interface port1 ingress_policing_burst=100
```

结果如下：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/after_1M.png)

```shell
#带宽上限为10mb
# ovs-vsctl set interface port1 ingress_policing_rate=10000
# ovs-vsctl set interface port1 ingress_policing_burst=1000
```

结果如下：

![image](https://github.com/Ewardnewget/OSlab/raw/master/第4次作业/pic/after_10M.png)

结果分析：可以看到带宽收到了明显的限制，但仍未达到最大带宽，原因可能是测试未到达上限或者最大突发流量限制。



#### 参考资料

[GRE and VXLAN with Open vSwitch](http://blog.sina.com.cn/s/blog_4b5039210102v2ft.html)

[Open vSwitch之QoS的实现](https://www.sdnlab.com/19208.html)

[openvswitch的原理和常用命令](http://www.cnblogs.com/wanstack/p/7606416.html)

[Vxlan学习笔记——原理](http://www.cnblogs.com/hbgzy/p/5279269.html)

[GRE与Vxlan网络详解](http://www.cnblogs.com/xingyun/p/4620727.html)

课件链接
