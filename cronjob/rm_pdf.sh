#!/bin/bash

cd /home/work/proj/thepast/var/down/pdf && {
    find ./ -name "*.pdf" -ctime +1 -exec rm {} \;
}
