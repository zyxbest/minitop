## minitop 


#### 要求
- 实现必要的几个输出如：users，uptime，load，cpu，memory，process
- 其他方面请尽量还原原有 top
- 展现形式可以不用实时刷新
- 实现上尽量高效(不要使用 ps 等命令)
- 可以用任何语言实现，Bash、Python or Go

#### 认识问题
1. "本质上是一个top的subnet，包含部分功能。" by interviewer
2. 从定位上看，作为一个Ops tool，Bash和Go是最合适的（效率、兼容性等），但Go不够熟悉，Bash过得去，最精通的Python不太适合做，需要权衡。结论：先用py快速实现一个可用版，做个评估先。
3. 高效意味着需要以更接近底层的方式实现？那么如果使用python一些已封装好的模块（如psutil）等就需要谨慎考量了。——另一方面来看，单纯用第三方模块，意义也不大，不过是拼命调包然后format，那也太简（ruo）单（zhi）了一些。Be careful,boy.
4. 其他方面包含的比较广，比如排序，比如显示命令，这些都是对已获取信息的组织、呈现，属于编码过程中的part2。

#### 准备
1. 实现原理：根据以往经验，很可能是通过/proc 来实现的，虽然事先已经手工验证得差不多（网上也有不少人这么说），最好能让源码背书，如果官方都这么做，说明这是一个完全可用的方法。

2. 验证：去下载procps的源码 https://gitlab.com/procps-ng/procps ，看了`top.c`和`sysinfo.c`，果然是对`/proc`下面的文件做一些读取和展示操作，这样就简单了，如果全都是IO操作，效率也是可以得到保障的，这样一来我们就有了一个足够稳固的standpoint。

3. 接下来就是coding, 注意事项：
    * macOS没有对应的目录，内核问题导致具体机制不同。
    * 避免使用第三方包
    * 作为一个子集，不要顺手加新功能，会有过度设计的嫌疑



#### 开发步骤
1. Dev：一个简单的python文件，通过功能测试
2. Package：打包成bin
3. Benchmarking：做一定的性能评估与各平台兼容性测试
4. Doc：整理readme，快速下载，使用


#### TODO
0. 编码
1. 传参：支持进程排序
2. 传参：支持显示每个CPU的独立状态
3. 

#### 参考文档
* http://www.linuxhowtos.org/manpages/5/proc.htm



