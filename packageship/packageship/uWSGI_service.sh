#!/bin/bash
SYS_PATH=/etc/pkgship/

function get_config(){
    cat $SYS_PATH/package.ini | grep -E ^$2 | sed s/[[:space:]]//g | awk 'BEGIN{FS="="}{print $2}' > config_file
}

function create_config_file(){
    echo "config type is: $config_type"
    get_config "$config_type" "daemonize"
    daemonize=$(cat config_file)
    get_config "$config_type" "buffer-size"
    buffer_size=$(cat config_file)
    wsgi_file_path=$(find /usr/lib/ -name "packageship")
    if [ $config_type = "manage" -o $config_type = "all" ];then
        get_config "$config_type" "write_port"
        write_port=$(cat config_file)
        get_config "$config_type" "write_ip_addr"
        write_ip_addr=$(cat config_file)
        echo "manage.ini:"
        echo "[uwsgi]
http=$write_ip_addr:$write_port
module=packageship.manage
wsgi-file=$wsgi_file_path/manage.py
callable=app
buffer-size=$buffer_size
daemonize=$daemonize" > manage.ini
        cat manage.ini
    fi
    
    if [ $config_type = "selfpkg" -o $config_type = "all" ];then
        get_config "$config_type" "query_port"
        query_port=$(cat config_file)
        get_config "$config_type" "query_ip_addr"
        query_ip_addr=$(cat config_file)
        echo "selfpkg.ini:"
        echo "[uwsgi]
http=$query_ip_addr:$query_port
module=packageship.selfpkg
wsgi-file=$wsgi_file_path/selfpkg.py
callable=app
buffer-size=$buffer_size
daemonize=$daemonize" > selfpkg.ini
        cat selfpkg.ini

    fi

}

if [ ! -n "$1" ]
then
	echo "Usages: sh packageship.sh [start|stop|restart]"
	exit 0
fi

if [ X$2 = X ];then
    config_type="all"
elif [ $2 = "manage" -o $2 = "selfpkg" ];then
    config_type=$2
else
    echo "can not phase the input of $2"
    exit 0
fi

create_config_file $config_type

if [ $1 = start ]
then
	psid=`ps aux | grep "uwsgi" | grep -v "grep" | wc -l`
	if [ $psid -gt 4 ]
	then
		echo "uwsgi is running!"
		exit 0
	else
		uwsgi -d --ini /etc/pkgship/manage.ini
		uwsgi -d --ini /etc/pkgship/selfpkg.ini
		echo "Start uwsgi service [OK]"
	fi


elif [ $1 = stop ];then
	killall -9 uwsgi
	echo "Stop uwsgi service [OK]"
elif [ $1 = restart ];then
	killall -9 uwsgi
	uwsgi -d --ini /etc/pkgship/manage.ini
	uwsgi -d --ini /etc/pkgship/selfpkg.ini
	echo "Restart uwsgi service [OK]"

else
	echo "Usages: sh packageship.sh [start|stop|restart]"
fi

