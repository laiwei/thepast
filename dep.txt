
sudo apt-get install python-virtualenv python-pip
sudo apt-get install git ipython
sudo apt-get install mysql-server 
#root password:password
mysql_secure_installation

sudo apt-get install python-mysqldb
#cd env/lib/python2.6/ && ln -s /usr/lib/pymodules/python2.6/MySQLdb/ MySQLdb && ln -s /usr/lib/pymodules/python2.6/_mysql_exceptions.py _mysql_exceptions.py && ln -s /usr/lib/pymodules/python2.6/_mysql.so _mysql.so

##cd env/lib/python2.7
##ln -s /usr/lib/python2.7/dist-packages/MySQLdb MySQLdb
##ln -s /usr/lib/python2.7/dist-packages/_mysql_exceptions.py  _mysql_exceptions.py
##ln -s /usr/lib/python2.7/dist-packages/_mysql.so _mysql.so


#redis not use any more, instead by memcached and mongodb
#sudo apt-get install redis-server

git clone git://github.com/laiwei/thepast.git
#virtualenv --no-site-packages env
virtualenv env

pip install flask redis tweepy httplib2


## mysql dump schema
mysqldump -u root -pmypassword test_database --no-data=true --add-drop-table=false > schema_dump.sql  

## mysql dump data
mysqldump -u root -pmypassword test_database --add-drop-table=false > data_dump.sql  

## import table
create database `thepast`
mysql -u root -ppassword thepast < past/schema.sql

##install nginx
###http://wiki.nginx.org/Install
sudo -s
nginx=stable # use nginx=development for latest development version
echo "deb http://ppa.launchpad.net/nginx/$nginx/ubuntu lucid main" > /etc/apt/sources.list.d/nginx-$nginx-lucid.list
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C300EE8C

apt-get update 
apt-get install nginx

##deploy with nginx and uwsgi
###http://projects.unbit.it/uwsgi/wiki/Quickstart
apt-get install build-essential python-dev libxml2-dev
pip install uwsgi

## run app
#uwsgi --socket 127.0.0.1:3031 --file /home/work/proj/thepast/pastme.py --callable app --processes 2
#or
#uwsgi -s /tmp/uwsgi.sock --file /home/work/proj/thepast/pastme.py --callable app --processes 2
#recommend
nohup uwsgi -s /tmp/uwsgi.sock --file /home/work/proj/thepast/pastme.py --callable app --processes 2 &

## xhtml2pdf
git clone git://github.com/chrisglass/xhtml2pdf.git
cd xhtml2pdf/
#modify requirements.xml, == to >=
pip install -r requirements.xml 
python setup.py install 

### for test
sudo apt-get install python-nose
nosetests --with-coverage


## PIL setup

sudo apt-get install libfreetype6-dev libjpeg8-dev
sudo ln -s /usr/lib/i386-linux-gnu/libz.so /usr/lib/
sudo ln -s /usr/lib/i386-linux-gnu/libfreetype.so.6 /usr/lib/
sudo ln -s /usr/lib/i386-linux-gnu/libjpeg.so /usr/lib/

#sudo ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
#sudo ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
#sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/

#pip install -U PIL
pip install --no-index -f http://dist.plone.org/thirdparty/ -U PIL


## config cache
## use redis instead memcached (no use any more)
### /etc/redis_7379.conf include ^/deploy/redis_cache.conf
### cp /etc/init.d/redis_6379 /etc/init.d/redis_7379
### sudo update-rc.d redis_7379 defaults

##mongo db
## sudo apt-get install mongodb-server
wget http://fastdl.mongodb.org/linux/mongodb-linux-i686-2.0.3.tgz
sudo mkdir -p /data/db
tar xzf mongodb-linux-i686-2.0.3.tgz
./mongodb-xxxx/bin/mongod &

pip install pymongo

## about mongodb
http://www.mongodb.org/display/DOCS/Advanced+Queries#AdvancedQueries
http://www.mongodb.org/display/DOCS/Optimization
##index
http://www.mongodb.org/display/DOCS/Indexes
http://blog.nosqlfan.com/html/271.html

db.thepast.getIndexes
db.thepast.ensureIndex({k:1})


## memcached
sudo apt-get install memcached
## edit /etc/memcached.conf, -m 100 means max-memory = 100M
## sudo /etc/init.d/memcached restart
## telnet 127.0.0.1 11211 "stats"
pip install python-memcached


## rss feed parse
pip install feedparser
#http://stackoverflow.com/questions/2244836/rss-feed-parser-library-in-python
#http://packages.python.org/feedparser/

## add note
pip install markdown2
https://github.com/trentm/python-markdown2


