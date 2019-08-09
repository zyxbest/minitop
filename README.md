## minitop 





#### requirement
* Linux kernel os
* Python 2.7+
* Partly support Python 3 (Still have format issues yet)
* No third-party-package requirement.

#### usage
```
git clone https://github.com/qrr1995/minitop
cd minitop
python minitop.py
```

sample output:
```
------------------------------------------------------------------------------------------------
|uptime       : 1days 7:5:23                                                                    |
|users        : 2                                                                               |
|load average : 0.00,0.11,0.24                                                                  |
|Cpu(s)       : 4.53 us,  3.04 sy,  0.01 ni, 92.23 id,  0.11 wa,  0.00 hi,  0.09 si,  0.00 st   |
|KiB Mem      : 4039668 total, 1027652 free, 630804 used, 2381212 buff/cache, 3026796 avail Mem |
|KiB Swap     : 0 total, 0 free, 0 used                                                         |
------------------------------------------------------------------------------------------------
Tasks: 139 total,   1 running,  94 sleeping,   0 stopped,   0 zombie
  PID USER      PR   NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
------------------------------------------------------------------------------------------------
 2848 root      20    0  406788 268208  66836 S   2.8   6.6    52:5.89 kube-apiserver
 1183 root      20    0  706416 104052  63744 S   3.9   2.6   71:53.38 kubelet
 2982 root      20    0  216864  96936  55736 S   1.5   2.4   28:18.31 kube-controller
 1438 root      20    0  599792  88676  37716 S   1.3   2.2   24:45.54 dockerd
 2766 root      20    010554916  52080  17816 S   1.6   1.3   30:46.79 etcd
 1414 root      20    0 1167140  45016  24952 S   0.2   1.1     3:17.7 containerd
 2916 root      20    0  141508  36956  27212 S   0.1   0.9    2:40.98 kube-scheduler
 5250 root      20    0  142288  32424  25460 S   0.3   0.8    5:56.32 coredns
 5028 root      20    0  142288  32176  25140 S   0.3   0.8    6:11.29 coredns
 3886 root      20    0  138988  31724  24408 S   0.1   0.8    1:33.86 kube-proxy
 4223 root      20    0  332564  28680  21780 S   0.1   0.7    1:23.85 flanneld
```


Also you could place the py into bin dir,since it's a single py script.
```
chmod +x minitop.py
sudo mv minitop.py /usr/bin/minitop
minitop
```

Keep watching minitop by 1 second fresh-interval
```
watch -n 1 minitop
```

Sort  by memory
```
minitop -s M 
```

Show top 10 most cpu used processes
```
minitop -s P -l 10
```

Show all processes sorted by memory usage.
```
minitop -s M -l -1
```




## 解题思路
#### 要求
- 实现必要的几个输出如：users,uptime,load,cpu,memory,process
- 其他方面请尽量还原原有 top
- 展现形式可以不用实时刷新
- 实现上尽量高效(不要使用 ps 等命令)
- 可以用任何语言实现，Bash、Python or Go

#### 解析与基本假设
1. "本质上是一个top的subnet，包含部分功能。" by interviewer
2. 从定位上看，作为一个Ops tool，Bash和Go是最合适的（效率、兼容性等），但Go不够熟悉，Bash过得去，最精通的Python不太适合做，需要权衡。结论：先用py快速实现一个可用版，做个评估先。
3. 高效意味着需要以更接近底层的方式实现？那么如果使用python一些已封装好的模块（如psutil）等就需要谨慎考量了。——另一方面来看，单纯用第三方模块，意义也不大，不过是拼命调包然后format，那也太简（ruo）单（zhi）了一些。Be careful,boy.
4. 其他方面包含的比较广，比如排序，比如显示命令等，这些都是对已获取信息的组织、呈现，属于编码过程中的part2，一律作为次优先feature来实现。
5. 关于显示的column选取，由于top能够显示的信息过多（最多高达50项），选定当前版本边界为实现top的默认视图，即包含以下示例信息即可：
```
Tasks: 136 total,   1 running,  95 sleeping,   0 stopped,   0 zombie
%Cpu(s):  5.9 us,  0.0 sy,  0.0 ni, 94.1 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem :  4039668 total,  1237124 free,   613512 used,  2189032 buff/cache
KiB Swap:        0 total,        0 free,        0 used.  3065216 avail Mem 

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND                        
    1 root      20   0   37996   5980   3928 S   0.0  0.1   2:47.72 systemd                        
    2 root      20   0       0      0      0 S   0.0  0.0   0:00.01 kthreadd                       
    4 root       0 -20       0      0      0 I   0.0  0.0   0:00.00 kworker/0:0H                   
    6 root       0 -20       0      0      0 I   0.0  0.0   0:00.00 mm_percpu_wq                   
    7 root      20   0       0      0      0 S   0.0  0.0   0:08.71 ksoftirqd/0                    
    8 root      20   0       0      0      0 I   0.0  0.0   0:38.53 rcu_sched          
```

#### 准备
1. 实现原理：根据以往经验，很可能是通过/proc 来实现的，虽然事先已经手工验证得差不多（网上也有不少人这么说），最好确认官方也是这么做的，说明这是一个完全可用的方法，不存在隐患。
2. 验证：去下载procps的源码 https://gitlab.com/procps-ng/procps ，看了`top.c`和`sysinfo.c`，果然是对`/proc`下面的文件做一些读取和展示操作，这样就简单了，如果全都是IO操作，效率也是可以得到保障的，有个稳固的出发点，且部分代码逻辑可参考。
3. 接下来就是coding, 注意事项：
    * macOS没有对应的目录，内核问题导致具体机制不同。
    * 避免使用第三方包
    * 作为一个子集，不应顺手加新功能

#### TODO
* [x] 传参：支持内存、cpu排序，编码样式可扩展，后续其他key容易传入
* [ ] 支持读取二进制文件来获取用户数，而不是用os.system来执行w命令 
* [ ] 传参：支持显示每个CPU的独立状态
* [ ] 支持动态刷新，以更科学地计算CPU使用率
* [ ] 更多的测试
* [ ] 输出样式上的细节,比如大数、时间的单位转换等。
* [ ] 计算CPU时间的函数，需要获取hertz参数，目前用的是os.system执行`getconf CLK_TCK`命令，除了C语言调用的相关库之外，是否存在更好的获得方式？
* [ ] 类似地，计算shared memory时将page转化为memory，用的pagesize也是用`getconf PAGESIZE`获取的。
* [ ] 更好的打包方式（现在牺牲可读性将所有函数放一个py里）

#### 参考资料
* http://man7.org/linux/man-pages/man1/top.1.html
* http://man7.org/linux/man-pages/man5/proc.5.html
* https://zh.wikipedia.org/wiki/Procfs
* https://gitlab.com/procps-ng/procps/blob/master/proc/readproc.c
* https://stackoverflow.com/questions/16726779/how-do-i-get-the-total-cpu-usage-of-an-application-from-proc-pid-stat


