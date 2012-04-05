个人杂志计划
=============

我在业余时间，做了一个小小的开源项目，叫做个人杂志计划。

目前在做的功能：
-------

* 实时聚合个人在豆瓣广播，新浪微博，twitter，腾讯微博的内容，并生成排版后的PDF文件，可供下载。

个人杂志计划的目的：
-------

* 一方面可以永久保存自己的timeline到本地。
* 另一方面，排版后的PDF版本，在移动设备上(手机，pad)的离线阅读体验很不错，或者发送到kindle上。
* 此外，如果我们还有精力的话，不妨把排版做的更好，这样出一本记录自己，讲述自己的纸质杂志应该还是很令人期待的。

还有一些更多可以做的东西：
-------

* 聚合更多的内容，包括饭否，wordpress……
* 对聚合后的消息，提供搜索功能(个人信息的社会化搜索)
* 对聚合后的消息，做去重
* PDF排版，更美观
* 如何做纸质的杂志，包括版式设计，排版，打印
* 延伸一点，可以根据聚合后的timeline，生成更权威的“个人关键字tag云”
* 提供名片的功能，可以补充自己的信息，展示出来

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


作为开源项目，期待大家加入，也欢迎吐槽。

贡献者列表：
-------
* [laiwei](https://github.com/laiwei) --`项目发起者` 
* [lmm214](https://github.com/lmm214) --`设计，修改了首页timeline的展示方式` 


ChangeList:
-------
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
