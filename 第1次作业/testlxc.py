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

#create file in the root dir
c.attach_wait(lxc.attach_run_command,["touch","Hello-Container"])
c.attach_wait(lxc.attach_run_command,["bash","-c",'echo "姓名：祝世豪\n学号：1500012848" >Hello-Container'])

#stop the container
if not c.shutdown(5):
    c.stop()
