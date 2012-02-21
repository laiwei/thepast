个人杂志计划
=============

我在业余时间，做了一个小小的开源项目，叫做个人杂志计划。

目前在做的功能：
-------

* 聚合个人在豆瓣广播，新浪微博，twitter的内容，并生成排版后的PDF文件，可供下载。

个人杂志计划的目的：
-------

* 一方面可以永久保存自己的timeline到本地。
* 另一方面，排版后的PDF版本，在移动设备上(手机，pad)的离线阅读体验很不错，或者发送到kindle上。
* 此外，如果我们还有精力的话，不妨把排版做的更好，这样出一本记录自己，讲述自己的纸质杂志应该还是很令人期待的。

还有一些更多可以做的东西：
-------

* 聚合更多的内容，包括饭否，腾讯微博，wordpress……
* 对聚合后的消息，提供搜索功能
* 对聚合后的消息，做去重
* PDF排版，更美观
* 如何做纸质的杂志，包括版式设计，排版，打印

技术细节：
-------

* [linux(debian6)](http://debian.org) -- `stable and powerfull`
* nginx/uwsgi -- `web server and serve static file`
* mysql
* python
* [flask](http://flask.pocoo.org) -- `python web framework`
* [redis](http://redis.io) -- `nosqldb, store text,img etc, and used for cache instead of memcached`
* [xhtml2pdf](https://github.com/chrisglass/xhtml2pdf) -- `convert html to pdf`
* git/github -- `code version control`
* v2ex -- `thanks for v2ex and css of v2ex^^`

项目地址：
-------

https://github.com/laiwei/thepast

官方主页： 
-------

http://thepast.me


作为开源项目，期待大家加入，也欢迎吐槽。

thanks

by laiwei
