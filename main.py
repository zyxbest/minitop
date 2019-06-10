# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yixuan Zhao <johnsonqrr (at) gmail.com>

import os
import sys
import time
import datetime
# todo: receive OPTIONS

'''
top - 06:43:16 up  2:24,  1 user,  load average: 0.45, 0.42, 0.36
Tasks: 138 total,   1 running,  93 sleeping,   0 stopped,   0 zombie
%Cpu(s):  7.3 us,  4.8 sy,  0.0 ni, 87.6 id,  0.0 wa,  0.0 hi,  0.3 si,  0.0 st
KiB Mem :  4039668 total,  2169404 free,   615920 used,  1254344 buff/cache
KiB Swap:        0 total,        0 free,        0 used.  3101644 avail Mem 
'''


STAT_FILE = "/proc/stat"

USERS_KEY = "users"
USERINFO_FILE = "/var/run/utmp"

UPTIME_KEY = "uptime"
UPTIME_FILE = "/proc/uptime"

LOADAVG_KEY = "load average"
LOADAVG_FILE = "/proc/loadavg"

MEMINFO_FILE = "/proc/meminfo"
MEMINFO_KEY = "KiB Mem "
SWAP_KEY = "KiB Swap"

CPU_KEY = "Cpu(s)"
CPUSTAT_FILE = "/proc/stat"


def output_info(info_key, info_value, newline=True):
    print "|{:12s} : {:80s}|".format(info_key, info_value)


def read_info_file(file_path):
    # 这里假设了涉及到的单个文件不会太大，直接传输整个文本
    with open(file_path, 'r') as f:
        return f.read()


def get_uptime():
    # 只有一行，第一列是启动时间，第二列是空闲时间（是cputime，后者可能大于前者）
    # eg:3241.45 5922.55
    uptime_in_secs = read_info_file(UPTIME_FILE).split()[0]

    return str(datetime.timedelta(seconds=int(float(uptime_in_secs))))


def get_users():
    return len(read_info_file(USERINFO_FILE).split()) - 1


def get_loadavg():
    return ' '.join(read_info_file(LOADAVG_FILE).split()[:3])


def get_cpu(detailed=False):
    # TODO:传参显示每个CPU的使用率
    cpu_info_format = '{user:.2f} us,  {system:.2f} sy,  {nice:.2f} ni, {idle:.2f} id,  {wa:.2f} wa,  {hi:.2f} hi,  {si:.2f} si,  {st:.2f} st'
    total_cpu_info = read_info_file(CPUSTAT_FILE).split('\n')[0].strip()
    cuser, cnice, csystem, cidle, ciow, chirq, csirq, csteal, cguest, cguest_nice  = \
        [int(item) for item in total_cpu_info.split()[1:]]

    total_jiffies = float(cuser + csystem + cnice +
                          cidle + ciow + chirq + csirq)

    return cpu_info_format.format(
        user=cuser / total_jiffies * 100,
        system=csystem / total_jiffies * 100,
        nice=cnice / total_jiffies * 100,
        idle=cidle / total_jiffies * 100,
        wa=ciow / total_jiffies * 100,
        hi=chirq / total_jiffies * 100,
        si=csirq / total_jiffies * 100,
        st=csteal / total_jiffies * 100
    )


def get_mem():
    '''
    ref code: https://gitlab.com/procps-ng/procps/blob/master/proc/sysinfo.c#L698

    example data:
        ```
        MemTotal:        4039668 kB
        MemFree:         2131156 kB
        MemAvailable:    3089376 kB
        Buffers:          104508 kB
        Cached:           961788 kB
        ...
        ```
    MemTotal - MemUsed = MemFree + buff/cache(Buffers + Cached +Slab)

    see `man free`: 
    cache  Memory used by the page cache and slabs (Cached and Slab in /proc/meminfo)
    '''
    meminfo_str = '{total} total, {free} free, {used} used, {buff_cache} buff/cache, {avail} avail Mem'
    swap_info_str = '{swap_total} total, {swap_free} free, {swap_used} used'

    # generate all k-v pairs from meminfo
    meminfo_dict = {}

    for line in read_info_file(MEMINFO_FILE).split('\n'):
        if not line:
            continue
        k, v = line.split(':')[:2]
        v = v.split()[0]
        meminfo_dict[k] = v.strip()

    # Get meminfo
    total = meminfo_dict.get('MemTotal', 0)
    free = meminfo_dict.get('MemFree', 0)
    buff = meminfo_dict.get('Buffers', 0)
    cached = meminfo_dict.get('Cached', 0)
    slab = meminfo_dict.get('Slab', 0)

    buff_cache = int(buff) + int(cached) + int(slab)
    used = int(total) - int(free) - buff_cache
    avail = meminfo_dict.get('MemAvailable', 0)
    meminfo_res = meminfo_str.format(
        total=total,
        free=free,
        used=used,
        buff_cache=buff_cache,
        avail=avail
    )

    # Get swap info
    swap_total = int(meminfo_dict.get('SwapTotal', 0))
    swap_free = int(meminfo_dict.get('SwapFree', 0))
    swap_used = swap_total - swap_free

    swap_info_res = swap_info_str.format(
        swap_total=swap_total,
        swap_free=swap_free,
        swap_used=swap_used
    )
    return meminfo_res, swap_info_res


def get_system_info():
    print "-" * 95

    uptime_str = get_uptime()
    output_info(UPTIME_KEY, uptime_str)

    users_num_str = str(get_users())
    output_info(USERS_KEY, users_num_str)

    load_str = get_loadavg()
    output_info(LOADAVG_KEY, load_str)

    cpu_str = get_cpu()
    output_info(CPU_KEY, cpu_str)

    mem_str, swap_mem_str = get_mem()
    output_info(MEMINFO_KEY, mem_str)

    output_info(SWAP_KEY, swap_mem_str)

    print "-" * 82


def get_process_info():
    pass


def main():
    get_system_info()
    get_process_info()


if __name__ == '__main__':
    main()
