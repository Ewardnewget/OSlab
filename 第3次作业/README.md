### 第三次作业

#### 1. 叙述课件第一张图中的Linux网络包处理流程

iptables的功能主要由三种重要结构提供：tables、chains、targets   

tables：  

| tables        | functions                              |
| ------------- | -------------------------------------- |
| filter tables | 用于对packet进行过滤                   |
| mangle tables | 修改packet头，用于指定如何处理数据包等 |
| raw tables    | 决定数据包是否被状态跟踪机制处理       |
| nat tables    | 用于网络地址转换，可用于转发packet     |

chains：

| chains      | functions                            |
| ----------- | ------------------------------------ |
| INPUT       | 对接受的数据包应用此链的规则         |
| OUTPUT      | 对发送出去的数据包应用此链的规则     |
| FORWARD     | 对转发的数据包应用此链的规则         |
| PREROUTING  | 对数据包做路由选择之前应用此链的规则 |
| POSTROUTING | 对数据包做路由选择之后应用此链的规则 |

  

每条链可以包含一条或者多条规则，当一个数据包到达一个链时，iptables按照顺序对数据包进行规则检查，如果match，则按照规则制定的处理策略处理该包；如果没有match，则继续进行下一条规则的检查；如果该数据包不符合链中的任意一条规则，则根据默认策略处理。  

不同的链中规则表有不同的优先顺序  

1. 接受数据流向：从外界到达的数据包，先被PREROUTING规则链处理（是否修改数据包地址等），之后会进行路由选择（判断该数据包应该发往何处），如果数据包 的目标主机是本机，那么将其传给INPUT链进行处理（过滤并决定处理策略等），通过以后再交给相应进程。
2. 转发数据流向： 来自外界的数据包到达后，首先被PREROUTING规则链处理，之后会进行路由选择，如果数据包的目标地址是外部地址，则将其传递给FORWARD链进行处理（是否转发或拦截），然后再交给POSTROUTING规则链（是否修改数据包的地址等）进行处理。
3. 外发数据流向： 本机向外部地址发送的数据包，首先被OUTPUT规则链处理，之后进行路由选择，然后传递给POSTROUTING规则链（是否修改数据包的地址等）进行处理。


#### 2. 在服务器上使用[iptables](http://cn.linux.vbird.org/linux_server/0250simple_firewall.php)分别实现如下功能并测试：

##### 1）拒绝来自某一特定IP地址的访问；

sudo iptables -A INPUT -s 192.168.202.131 -j DROP

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/refuse.png)

##### 2）只开放本机的http和ssh服务，其余协议与端口均拒绝；

sudo iptables -P INPUT DROP

sudo iptables -P FORWARD DROP

sudo iptables -P OUTPUT DROP

sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

sudo iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT

sudo iptables -A INPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT

sudo iptables -A OUTPUT -p tcp --sport 80 -m state --state NEW,ESTABLISHED -j ACCEPT

拒绝所有访问

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/refuse_all.png)
 
开放ssh和http

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/open_ssh_http.png)

测试ssh

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/ssh_open.png)

##### 3）拒绝回应来自某一特定IP地址的ping命令;

sudo iptables -I OUTPUT -s 192.168.202.131 -p icmp --icmp-type echo-reply -j DROP

![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/refuse_ping.png)

#### 3. 解释路由与交换这两个概念的区别，并介绍bridge, veth这两种Linux网络设备的工作原理

##### 区别：  

1. 工作层次不同：交换机工作在数据链路层（第二层），路由器工作在网络层（第三层），相应的二者识别的地址也不同，交换机只能识别MAC地址，常用于局域网段互联，路由器能够识别IP地址， IP地址由网络管理员分配，是逻辑地址且具有层次结构，被划分成网络号和主机号，可以非常方便地用于划分子网，路由器的主要功能就是用于连接不同的网络。
2. 数据通路结构不同：交换机之间不允许存在回路，而交换机允许贿赂的存在，且回路能够更好地进行负载平衡，因此交换机负载更为集中，路由器负载更加均衡。
3. 主要功能不同：交换机作为桥接设备也能完成不同链路层和物理层之间的转换，但这种转换过程比较复杂，会降低交换机的转发速度。因此目前交换机主要完成相同或相似物理介质和链路协议的网络互连； 而路由器主要用于不同网络之间互连，因此能连接不同物理介质、链路层协议和网络层协议的网络。

##### bridge  

Bridge是 Linux 上用来做 TCP/IP 二层协议交换的设备，是一个虚拟交换机，和物理交换机有类似的功能，但是与单纯的交换机不同，交换机只是一个二层设备，对于接收到的报文，要么转发、要么丢弃；而运行着linux内核的机器本身就是一台主机，有可能就是网络报文的目的地，网桥收到的报文除了转发和丢弃，还可能被送到网络协议栈的上层（网络层）。

bridge主要功能为MAC地址学习和报文转发。bridge可以attach若干网络设备，从而将它们桥接起来，bridge有相应的数据结构维护其连接的设备, 端口链表, 转发表。bridge收到数据包后根据MAC地址进行匹配，若匹配成功则转发至目的端口，否则进行广播。

##### veth  

veth是linux中的一种虚拟网络设备，通常成对出现，一端连接的是内核协议栈，另一端两个设备彼此相连，一个设备收到协议栈的数据发送请求后，会将数据发送到另一个设备上去。主要作用是完成数据注入。

bridge和veth广泛用于虚拟机技术和容器技术，实现虚拟机和容器与宿主机网络设备的数据传输，从而能够访问外部网络。

#### 4.

##### 1）按照课件描述的结构图在上节课fakeContainer的基础上为其增加网络功能，使fakeContainer内部可以访问Internet;

```
# in host
//创建bridge，并为bridge分配ip
sudo ip link add name br0 type bridge
sudo ip link set br0 up
sudo ip addr add 192.168.3.101/24 dev br0
//创建veth pair，将veth0 attach到bridge
sudo ip link add veth0 type veth peer name veth1
sudo ip link set dev veth0 master br0
sudo ip link set veth0 up
//将veth1与容器关联
sudo ip link set veth1 netns child_pid
```

```
# in container
//设置容器路由通过veth1连接外网
system("ip link set veth1 up");
system("ip route add default dev veth1");
system("ip addr add 192.168.3.102/24 dev veth1");
system("route add default gw 192.168.3.101");
```

 container ping host
 
 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/ping_host.PNG)
 
 host ping container
 
 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/ping_container.PNG)



```
# in host
//设置iptables规则，实现NAT，进行ip映射
system("sudo iptables -t nat -A POSTROUTING -s 192.168.3.102/24 -j MASQUERADE");
```

 ![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/ping_out.PNG)


##### 2）实现功能1)后在fakeContainer中部署一个nginx web服务器,使得可以通过服务器的公网IP访问到该nginx服务器web服务;

```
# in container
sudo apt-get install nginx
sudo /usr/sbin/nginx
sudo iptables -t nat -A PREROUTING -p tcp --dport 8888 -j DNAT --to-destination 192.168.3.102:80
```


![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/nginx.PNG)


##### 3)解释一个外部用户在从fakeContainer中nginx服务器得到web服务这个过程中，网络包在Linux服务器上经过了什么样的处理流程。

![image](https://github.com/Ewardnewget/OSlab/raw/master/第3次作业/pic/web.PNG)

如图，外部数据包通过eth0进入，经由iptables实现的NAT实现判定转发，判断目的ip为本机地址，将该数据包转发到INPUT链，之后根据端口转发，经由br0、veth0、veth1进入容器网络栈处理，处理结果经原路返回。
