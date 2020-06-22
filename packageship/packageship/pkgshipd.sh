#!/bin/bash
SYS_PATH=/etc/pkgship/
OUT_PATH=/var/run/pkgship_uwsgi
if [ ! -d "$OUT_PATH" ]; then
        mkdir $OUT_PATH
fi

function get_config(){
    cat $SYS_PATH/package.ini | grep -E ^$2 | sed s/[[:space:]]//g | awk 'BEGIN{FS="="}{print $2}'
}

function create_config_file(){
    echo "config type is: $service"
    daemonize=$(get_config "$service" "daemonize")
    buffer_size=$(get_config "$service" "buffer-size")
    wsgi_file_path=$(find /usr/lib/ -name "packageship")
    if [ $service = "manage" -o $service = "all" ];then
        write_port=$(get_config "$service" "write_port")
        write_ip_addr=$(get_config "$service" "write_ip_addr")
        echo "manage.ini is saved to $OUT_PATH/manage.ini"
        echo "[uwsgi]
http=$write_ip_addr:$write_port
module=packageship.manage
wsgi-file=$wsgi_file_path/manage.py
callable=app
buffer-size=$buffer_size
pidfile=$OUT_PATH/manage.pid
daemonize=$daemonize" > $OUT_PATH/manage.ini
    fi
    
    if [ $service = "selfpkg" -o $service = "all" ];then
        query_port=$(get_config "$service" "query_port")
        query_ip_addr=$(get_config "$service" "query_ip_addr")
        echo "selfpkg.ini is saved to $OUT_PATH/selfpkg.ini"
        echo "[uwsgi]
http=$query_ip_addr:$query_port
module=packageship.selfpkg
wsgi-file=$wsgi_file_path/selfpkg.py
callable=app
buffer-size=$buffer_size
pidfile=$OUT_PATH/selfpkg.pid
daemonize=$daemonize" > $OUT_PATH/selfpkg.ini

    fi

    rm -f config_file
}

function start_service(){
    if [ "`ps aux | grep "uwsgi" | grep "$1.ini"`" != "" ];then
        echo "!!!$1 service is running, please stop it first!!!"
    else
        uwsgi -d --ini $OUT_PATH/$1.ini
    fi
}

function stop_service(){
    pid=$(cat $OUT_PATH/$1.pid)
    if [ "`ps aux | awk 'BEGIN{FS=" "}{if ($2=='$pid') print $0}' | grep "$1.ini"`" != "" ];then
        uwsgi --$2 $OUT_PATH/$1.pid
    else
        echo "!!!STOP service [FAILED], Please start the service first!!!"
        echo "===If the service has already exist, Please stop it manually by using [ps -aux] and [uwsgi --stop #PID]"
}

if [ ! -n "$1" ]
then
	echo "Usages: sh packageship.sh [start|stop|restart]"
	exit 0
fi

if [ X$2 = X ];then
    service="all"
elif [ $2 = "manage" -o $2 = "selfpkg" ];then
    service=$2
else
    echo "!!!can not phase the input of $2!!!"
    exit 0
fi

create_config_file $service

if [ $1 = start ]
then
    if [ $service = "all" ];then
        start_service "manage"
        start_service "selfpkg"
    else
        start_service $service
    fi
    echo "===The run log is saved into $daemonize==="

elif [ $1 = stop ];then
    if [ $service = "all" ];then
        stop_service "manage" "stop"
        stop_service "selfpkg" "stop"
    else
        stop_service $service "stop"
    fi
    echo "===The run log is saved into $daemonize==="

elif [ $1 = restart ];then
    if [ $service = "all" ];then
        stop_service "manage" "reload"
        stop_service "selfpkg" "reload"
    else
        stop_service $service "reload"
    fi
    echo "===The run log is saved into $daemonize==="

else
	echo "Usages: sh packageship.sh [start|stop|restart]"
fi

