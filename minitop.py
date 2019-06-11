#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Yixuan Zhao <johnsonqrr (at) gmail.com>
from __future__ import print_function
from collections import Counter

import os
import datetime
import pwd
import argparse



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

read_proc_fail_msg = '''Error: /proc must be mounted
To mount /proc at boot you need an /etc/fstab line like: 
proc   /proc   proc    defaults
In the meantime, run \"mount proc /proc -t proc\"
'''

TOTAL_PHYSICAL_MEMORY = 0
UPTIME = 0
HERTZ = 100


def output_info(info_key, info_value, newline=True):
    print("|{:12s} : {:80s}|".format(info_key, info_value))


def read_file(file_path):
    # 这里假设了涉及到的单个文件不会太大，直接传输整个文本
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(read_proc_fail_msg)
        raise e


def get_uptime():
    # 第一列是启动时间，第二列是空闲时间（每个cpu累加计算，后者可能大于前者）
    # eg:3241.45 5922.55
    uptime_in_secs = read_file(UPTIME_FILE).split()[0]
    return float(uptime_in_secs)


def get_users():
    # not best implement
    return int(os.popen('w -h|wc -l ').read().strip())


def get_loadavg():
    return ','.join(read_file(LOADAVG_FILE).split()[:3])


def get_cpu(detailed=False):
    # TODO:传参显示每个CPU的使用率
    cpu_info_format = '{user:.2f} us,  {system:.2f} sy,  {nice:.2f} ni, {idle:.2f} id,  {wa:.2f} wa,  {hi:.2f} hi,  {si:.2f} si,  {st:.2f} st'
    total_cpu_info = read_file(CPUSTAT_FILE).split('\n')[0].strip()
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
    global TOTAL_PHYSICAL_MEMORY
    '''
    ref code: https://gitlab.com/procps-ng/procps/blob/master/proc/sysinfo.c#L698


    MemTotal - MemUsed = MemFree + buff/cache(Buffers + Cached +Slab)
    see `man free`: 
    cache  Memory used by the page cache and slabs (Cached and Slab in /proc/meminfo)
    '''
    meminfo_str = '{total} total, {free} free, {used} used, {buff_cache} buff/cache, {avail} avail Mem'
    swap_info_str = '{swap_total} total, {swap_free} free, {swap_used} used'

    # generate all k-v pairs from meminfo

    meminfo_dict = {}
    for line in read_file(MEMINFO_FILE).split('\n'):
        if not line:
            continue
        k, v = line.split(':')[:2]
        meminfo_dict[k] = int(v.split()[0])

    # Get meminfo
    TOTAL_PHYSICAL_MEMORY = total = meminfo_dict.get('MemTotal', 0)
    free = meminfo_dict.get('MemFree', 0)
    buff = meminfo_dict.get('Buffers', 0)
    cached = meminfo_dict.get('Cached', 0)
    slab = meminfo_dict.get('Slab', 0)

    buff_cache = buff + cached + slab
    used = total - free - buff_cache
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
    print("-" * 96)

    global UPTIME
    UPTIME = uptime_secs = get_uptime()
    uptime_secs = int(uptime_secs)
    uptime_str = '{}:{}:{}'.format(
        uptime_secs / 86400, uptime_secs % 86400 / 3600, uptime_secs % 3600)

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

    print("-" * 96)


def get_proc_status(pid):
    # see `/proc/pid/status` and `/proc/pid/stat`
    procs_status_file = "/proc/{}/stat".format(pid)
    proc_state = read_file(procs_status_file).split()[2]
    print(proc_state)


# May suport screen fresh  in FUTURE,see
# https://gitlab.com/procps-ng/procps/blob/master/ps/display.c#L322
def get_cpu_percent(procs_stat_list, include_childten=False):
    # cpu使用率 = cpu使用时间 / 进程启动至今时间
    # cpu使用时间 需要用Hertz来换算成秒
    # 启动至今时间 = 机器启动至今时长 - 进程启动时刻（从机器启动开始计算，因此可以作为时间间隔）
    used_jiffies = int(procs_stat_list[13]) + int(procs_stat_list[14])

    start_time = int(procs_stat_list[21])
    seconds = UPTIME - (start_time / HERTZ)

    # 如果要统计一段时间内的使用率，这里对cpu 时间和seconds取delta即可
    cpu_percent = 100 * ((used_jiffies / HERTZ) / seconds)
    return cpu_percent

#   used_jiffies = buf->utime + buf->stime;


# Generate a process dict from pid.
# Carefully looks up man page of proc(5) and top(1) which make all things easier!
# Notice the CPU definition： The task's share of the elapsed CPU time since the last screen update
# About Cpu,see
# https://gitlab.com/procps-ng/procps/blob/master/ps/display.c#L322
def get_item_by_pid(pid):
    procs_status_file = "/proc/{}/status".format(pid)

    pid_status_dict = {}
    for line in read_file(procs_status_file).split('\n'):
        if not line:
            continue
        k, v = [i.strip() for i in line.split(':', 1)]
        if not v:
            continue
        v = v.split()[0]
        pid_status_dict[k] = v

    user_uid = os.stat('/proc/{}'.format(pid)).st_uid
    user_name = pwd.getpwuid(user_uid)[0]

    # eg data : 1 (systemd) S 0 1 1 0 -1 4194560 23103 3398035 50 1125 12321 19185 10044 6227 20 0 1 0 4 38907904 1495 18446744073709551615 1 1 0 0 0 0 671173123 4096 1260 0 0 0 17 0 0 0 94 0 0 0 0 0 0 0 0 0 0
    # meaning: pid,comm,state,ppid,pgrp,session,tty,tpgid,9others,priority,nice
    procs_stat_file = "/proc/{}/stat".format(pid)
    procs_stat_list = read_file(procs_stat_file).split()
    cpu_percent = get_cpu_percent(procs_stat_list)

    item = {
        'name': pid_status_dict.get('Name', ''),
        'pid': pid,
        'user': user_name,
        'priority': procs_stat_list[17],
        'ni': procs_stat_list[18],
        'virt': pid_status_dict.get('VmSize', '0'),
        # RES = sum of (RSan + RSfd +RSsh) ,  get it from VmRSS key
        'res': pid_status_dict.get('VmRSS', '0'),
        'shr': int(pid_status_dict.get('RssShmem', '0')) + int(pid_status_dict.get('RssFile', '0')),
        'state': pid_status_dict.get('State', ''),
        'cpu_percent': cpu_percent,
        'mem_percent': 100 * float(pid_status_dict.get('VmRSS', '0')) / (TOTAL_PHYSICAL_MEMORY),
        'cpu_time': (int(procs_stat_list[13]) + int(procs_stat_list[14])) / float(HERTZ),
        'cmd': read_file("/proc/{}/cmdline".format(pid))
    }

    item['cpu_time'] = '{}:{}'.format(
        int(item['cpu_time']) / 60, item['cpu_time'] % 60)

    if item['priority'] == '-100':
        item['priority'] = 'rt'
    return item


def get_procs_list():
    procs_list = []
    # 假如使用迭代器，会损失排序等功能，这里选择一次性全取出来，在进程非常多的时候可能存在一定性能问题
    subdir_list = os.listdir('/proc')
    for subdir in subdir_list:
        # TODO: figure out what self and thread_self is
        if 'self' in subdir or not os.path.isdir('/proc/{}/attr'.format(subdir)):
            continue
        else:
            pid = subdir
            item = get_item_by_pid(pid)
            procs_list.append(item)

    return procs_list


def display_procs_list(procs_list, limit):
    print("  PID USER      PR   NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND")
    print("-" * 96)
    if limit == -1:
        limit = len(procs_list)

    for proc in procs_list[:limit]:
        print('{pid:>5} {user:<10}{pr:>2}{ni:>5}{virt:>8}{res:>7}{shr:>7}{s:>2}{cpu:>6.1f}{mem:>6.1f} {time:>10} {command}'.format(
            pid=proc.get('pid', ''),
            user=proc.get('user', ''),
            pr=proc.get('priority', ''),
            ni=proc.get('ni', ''),
            virt=proc.get('virt', ''),
            res=proc.get('res', ''),
            shr=proc.get('shr', ''),
            s=proc.get('state', ''),
            cpu=proc.get('cpu_percent', ''),
            mem=proc.get('mem_percent', ''),
            time=proc.get('cpu_time', ''),
            command=proc.get('name', '')
        ))
    print("-" * 96)


def set_hertz():
    global HERTZ
    try:
        HERTZ = int(os.popen('getconf CLK_TCK').read().strip())
    except Exception as e:
        print('fail to exec `getconf CLK_TCK` command, use default HERTZ value:{}'.format(HERTZ))
        raise e
    return True


def sort_procs_list(procs_list, sort_key):
    if sort_key in procs_list[0]:
        procs_list.sort(key=lambda item: item[sort_key], reverse=True)
    else:
        print('Ignore meaningless key: {}'.format(sort_key))
        return


def displey_procs_counter(procs_list):
    task_counter = Counter()
    for proc in procs_list:
        task_counter[proc['state']] += 1
    print('Tasks: {} total,   {} running,  {} sleeping,   {} stopped,   {} zombie'.format(
        len(procs_list),
        task_counter['R'],
        task_counter['S'],
        task_counter['T'],
        task_counter['Z']
    ))


def get_process_info(sort_key, limit, truncate=0):
    set_hertz()

    procs_list = get_procs_list()

    if sort_key:
        sort_procs_list(procs_list, sort_key=sort_key)

    displey_procs_counter(procs_list)
    display_procs_list(procs_list, limit=limit)


sort_key_map = {
    'M': 'mem_percent',
    'P': 'cpu_percent'
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--sort', help='sort key, choices: M for memory, P for cpu')
    parser.add_argument(
        '-l', '--limit', help='limit of the process, set to 20 by default, set to -1 as no limit')
    args = parser.parse_args().__dict__
    sort_key = sort_key_map.get(args.get('sort'))
    limit = int(args.get('limit') or '20')

    get_system_info()
    get_process_info(sort_key=sort_key, limit=limit)

if __name__ == '__main__':
    main()
