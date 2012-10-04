你好 旧时光 | 之个人杂志计划 
=============

当今的互联网，在高速发展，大家都在努力向前看！

thepast，希望能帮助我们，时不时的停住脚步，去看看过往的一些事情…


**目前已经完成的一些东西**：

1. 实时聚合个人在“豆瓣”、“人人”、“新浪微博”、“腾讯微博”、“Twitter”、“wordpress”、“instagram” 等平台的 Timeline（包括历史消息）。
1. 每天清晨，会邮件提醒你过往的今天都发生了些什么，或许是惊喜，亦或是怀念。
1. 聚合后的Timeline，生成PDF[预览]版本，供离线阅读或永久保存，打造你自己的个人杂志。
1. 同步更新微博到多个平台（有些偏离thepast的主旨，是提供给一小部分用户使用的）。
1. 提供日记功能，“今天写日记，明年再来看”。

**计划中的一些事情**：

1. 导入更多的第三方（evernote、google+、facebook）
1. 提供多种形式的导出形式（不仅仅是PDF形式，可能会支持导出到google drive，dropbox等）
1. 个人挑选的历史信息，转为纸质杂志，作为留念，收藏。
1. 设置个性域名，提供个人名片服务(在个人数据挖掘的基础上提供全面的个人名片)。
1. Android、iOS移动客户端，提供更好的历史消息回顾体验。 


还有一些更多可以做的东西：
-------
* 对聚合后的消息，提供搜索功能(个人信息的社会化搜索)
* 根据聚合后的timeline，生成更权威的“个人关键字tag云”
* 更好的排版格式，提升在移动设备上(手机，pad)的离线阅读体验，或者发送到kindle上也未尝不可。
* 试想想，这样出一本记录自己，讲述自己的纸质杂志应该还是很令人期待的。

**目前的运行状况**

- 注册用户2300+
- 用户数据500万条
- 绑定的sns帐号，4000+


技术细节：
-------

* [linux(debian6)](http://debian.org) -- `stable and powerfull`
* nginx/uwsgi -- `web server and serve static file`
* mysql
* python
* [flask](http://flask.pocoo.org) -- `python web framework`
* [redis](http://redis.io) -- `nosqldb, store text,img etc, and used for cache instead of memcached`
* memcached -- `之前使用redis代替memcached，不过redis在小内存情况下表现较差，所以选择使用memcached`
* mongodb -- `data storage`
* [xhtml2pdf](https://github.com/chrisglass/xhtml2pdf) -- `convert html to pdf`
* [scws](http://www.ftphp.com/scws) -- `simple chinese word segment`
* git/github -- `code version control`
* v2ex -- `thanks for v2ex and css of v2ex^^`

项目地址：
-------

https://github.com/laiwei/thepast

官方主页： 
-------

http://thepast.me


作为开源项目，欢迎前端工程师 和 iOS工程师，一起来完善，也欢迎吐槽。

贡献者列表：
-------
* [laiwei](https://github.com/laiwei) --`项目发起者` 
* [lmm214](https://github.com/lmm214) --`设计，修改了首页timeline的展示方式` 


ChangeList:
-------
* `2012-10-03`: 支持绑定instagram了:)
* `2012-10-02`: 支持绑定人人了:)
* `2012-09-11`: 数据存储从mongodb转向了mysql，节省硬盘空间，[参考](http://laiwei.net/2012/09/15/mongodb和mysql的一个小小的取舍比较)
* `2012-09-09`: “时间线”重构，使用flask的blueprint，松耦合；时间线支持reverse order
* `2012-07-24`: 支持从thepast发送消息到多个第三方了
* `2012-06-09`: 日记支持markdown格式，这样写日记方便好多了:)
* `2012-04-22`: 增加了隐私设置，可以选择公开、仅登录用户可见、仅自己可见，保护用户的隐私; 增加了邮件退订功能。
* `2012-04-18`: PDF归档，修改为按月归档，每个月生成一个独立的文件，代替了之前整理为一个PDF文件。
* `2012-04-14`: 增加了[“时间线”](http://thepast.me/visual)栏目，以一种别样的视角看过去。
* `2012-04-10`: 支持绑定自己的独立wordpress博客:)
* `2012-04-05`: 增加了"我的过去"栏目，提供有意思的回忆功能
* `2012-04-04`: 提供补充email功能，以便在PDF文件生成之后，通知用户或者直接发送附件
* `2012-04-01`: redis在内存比较小的情况下，效率比较低，而且在分配的内存耗尽，没有及时淘汰掉key时，会造成写入失败，于是改用了memcached
* `2012-04-01`: mongodb坏掉了，原因是在32位系统下，mongodb存在数据文件不能超过2G的限制，见[官方说明](http://blog.mongodb.org/post/137788967/32-bit-limitations); 于是将系统升级为64位debian，重新安装了64位版本mongodb，恢复了数据
* `2012-03-31`: 加上了sidebar，用来展示用户的自我介绍，个人关键字等
* `2012-03-30`: 恢复了早期新浪微博用户的status时间差了12小时的数据
* `2012-03-25`: 增加了个人关键字提取功能，根据timeline的信息提取个人关键字，使用了[scws](http://www.ftphp.com/scws/),thanks
* `2012-03-10`: 新的匿名用户首页和timeline页面,from木木[lmm214]
* `2012-03-04`: 使用mongodb代替redis做数据持久化存储,并将redis中的37万条数据转存到mongodb中
* `2012-03-04`: 使用豆瓣新广播的api，代替旧的miniblog API
* `2012-03-01`: mysql connect增加了mysql gone away之后的重试机制
* `2012-02-28`: 使用了新的logo，感谢木木[lmm214](https://github.com/lmm214)的设计
* `2012-02-24`: 支持同步腾讯微博(使用腾讯微博的朋友看过来^^)
* `2012-02-22`: 屏蔽搜索引擎收录(因为隐私还是很重要的)
* `2012-02-18`: 加cache，使用redis充当memcache，提高访问速度，降低机器负载
* `2012-02-17`: 优化PDF文件的下载效率，使用nginx来承担文件下载任务
* `2012-02-16`: 优化代码解决生成PDF的效率（因为内存不够用了^^）
* `2012-02-15`: 增加了个人杂志计划成员展示页
* `2012-02-14`: 在v2ex社区介绍个人杂志计划，共有40人加入！
* `2012-02-13`: 增加保存个人内容为排版后的PDF功能
* `2012-02-12`: 开源项目，个人杂志计划上线

thanks

by laiwei
