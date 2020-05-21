for file in `find upstream-info -name "*.yaml"`; do 
	grep version_control $file | egrep -q $1"[ \t]*$"
	if [ $? -eq 0 ]; then # found this
		name=`echo $file | awk -F/ '{print substr($0, index($0, $2))}' | sed -e "s/\.yaml//g"`
		echo $name
		#./check $name
	fi
done
