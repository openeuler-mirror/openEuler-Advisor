#!/bin/bash
SYS_PATH=/etc/pkgship/
OUT_PATH=/run/pkgship_uwsgi
if [ ! -d "$OUT_PATH" ]; then
        mkdir $OUT_PATH
fi

function get_config(){
    cat $SYS_PATH/package.ini | grep -E ^$2 | sed s/[[:space:]]//g | awk 'BEGIN{FS="="}{print $2}' > config_file
}

function create_config_file(){
    echo "config type is: $service"
    get_config "$service" "daemonize"
    daemonize=$(cat config_file)
    get_config "$service" "buffer-size"
    buffer_size=$(cat config_file)
    wsgi_file_path=$(find /usr/lib/ -name "packageship")
    if [ $service = "manage" -o $service = "all" ];then
        get_config "$service" "write_port"
        write_port=$(cat config_file)
        get_config "$service" "write_ip_addr"
        write_ip_addr=$(cat config_file)
        echo "manage.ini:"
        echo "[uwsgi]
http=$write_ip_addr:$write_port
module=packageship.manage
wsgi-file=$wsgi_file_path/manage.py
callable=app
buffer-size=$buffer_size
daemonize=$daemonize" > $OUT_PATH/manage.ini
        cat $OUT_PATH/manage.ini
    fi
    
    if [ $service = "selfpkg" -o $service = "all" ];then
        get_config "$service" "query_port"
        query_port=$(cat config_file)
        get_config "$service" "query_ip_addr"
        query_ip_addr=$(cat config_file)
        echo "selfpkg.ini:"
        echo "[uwsgi]
http=$query_ip_addr:$query_port
module=packageship.selfpkg
wsgi-file=$wsgi_file_path/selfpkg.py
callable=app
buffer-size=$buffer_size
daemonize=$daemonize" > $OUT_PATH/selfpkg.ini
        cat $OUT_PATH/selfpkg.ini

    fi

    rm -f config_file
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
    echo "can not phase the input of $2"
    exit 0
fi

create_config_file $service

if [ $1 = start ]
then
	psid=`ps aux | grep "uwsgi" | grep -v "grep" | wc -l`
	if [ $psid -gt 4 ]
	then
		echo "uwsgi is running!"
		exit 0
	else
		uwsgi -d --ini $OUT_PATH/manage.ini
		uwsgi -d --ini $OUT_PATH/selfpkg.ini
		echo "Start uwsgi service [OK], Please see the run log in $daemonize"
	fi


elif [ $1 = stop ];then
	killall -9 uwsgi
	echo "Stop uwsgi service [OK], Please see the run log in $daemonize"
elif [ $1 = restart ];then
	killall -9 uwsgi
	uwsgi -d --ini $OUT_PATH/manage.ini
	uwsgi -d --ini $OUT_PATH/selfpkg.ini
	echo "Restart uwsgi service [OK], Please see the run log in $daemonize"

else
	echo "Usages: sh packageship.sh [start|stop|restart]"
fi

