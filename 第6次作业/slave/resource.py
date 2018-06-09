#!/usr/bin/python
# coding:utf-8

import os
import json
import socket
import psutil


class Host:
    _hostname = socket.getfqdn(socket.gethostname())

    @classmethod
    def get_local_addr(cls):
        addr = socket.gethostbyname(cls._hostname)
        return addr

    @classmethod
    def get_hostname(cls):
        return cls._hostname

    @classmethod
    def ping(cls):
        result = os.system("ping -c 1 -w 1 %s >/dev/null" % cls.get_local_addr())
        if result == 0:
            return 1
        else:
            return 0


class CPU:
    @classmethod
    def _get_cpu_load(cls):
        # get cpu 5 minutes load
        loadavg = "/proc/loadavg"
        with open(loadavg) as f:
            con = f.read().split()
            return con[1]

    @classmethod
    def _get_cpu_usage(cls):
        # Return a float representing the current system-wide CPU utilization as a percentage
        return psutil.cpu_percent(interval=0.1)

    @classmethod
    def get_cpu_info(cls):
        cpu = {
            "cpuUtil": cls._get_cpu_load(),
            "cpuUsed": cls._get_cpu_usage()
        }
        return cpu


class Memory:
    mem = psutil.virtual_memory()

    @classmethod
    def _get_mem_total(cls):
        return cls.mem.total

    @classmethod
    def _get_mem_used(cls):
        return cls.mem.used

    @classmethod
    def get_mem_info(cls):
        mem = {
            "memUsed": cls._get_mem_used(),
            "memTotal": cls._get_mem_total(),
        }
        return mem


class NetworkCard:
    @classmethod
    def get_card_bytes_info(cls):
        # bytes_sent
        try:
            card_ip = []
            card_io = []
            interface = []
            for k, v in psutil.net_if_addrs().items():
                if k not in 'lo':
                    card_ip.append({'name': k, 'ip': v[0].address})

            for k, v in psutil.net_io_counters(pernic=True).items():
                if k not in 'lo':
                    card_io.append({'name': k, 'out': v.bytes_sent, 'in': v.bytes_recv})

            for i in range(len(card_ip)):
                card = {
                    'intName': card_io[i]['name'],
                    'ip': card_ip[i]['ip'],
                    'out': card_io[i]['out'],
                    'in': card_io[i]['in']
                }
                interface.append(card)
            return interface
        except AttributeError as e:
            print("Please use psutil version 3.0 or above")


class Disk:
    @classmethod
    def get_disk_info(cls):
        disklt = []
        for disk, sdiskio in psutil.disk_io_counters(perdisk=True, nowrap=False).items():
            if disk.startswith(('sd', 'vd')):
                device = '/dev/{}'.format(disk)
                capacity = psutil.disk_usage(device)
                diskdt = {
                    "diskName": device,
                    "total": capacity.total,
                    "used": capacity.used,
                    "ws": sdiskio.write_merged_count,
                    "rs": sdiskio.read_merged_count,
                    "wiops": sdiskio.write_count,
                    "riops": sdiskio.read_count,
                    "rkb": sdiskio.read_bytes / 1024,
                    "wkb": sdiskio.write_bytes / 1024
                }
                disklt.append(diskdt)
        return disklt


class Summary:
    def __init__(self):
        self._hostid = 1
        self._groupid = 1
        self._hostname = Host.get_hostname()
        self._ip = Host.get_local_addr()
        self._ping = Host.ping()
        self._cpu = CPU.get_cpu_info()
        self._memory = Memory.get_mem_info()
        self._network = NetworkCard.get_card_bytes_info()
        self._disk = Disk.get_disk_info()

    def start_collecting(self):
        summary = {
            'hostid': self._hostid,
            'groupid': self._groupid,
            'hostname': self._hostname,
            'ip': self._ip,
            'ping': self._ping,
            'cpu': self._cpu,
            'memory': self._memory,
            'network': self._network,
            'disk': self._disk
        }
        return summary

def get_resource_usage():
    c = Summary()
    return c.start_collecting()