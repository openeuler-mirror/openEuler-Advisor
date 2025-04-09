#!/usr/bin/env bash
#Config environment before develop, please run: source ./develop_env.sh

advisor_path=$(cd $(dirname ${BASH_SOURCE}); pwd)
python_paths=$(echo ${PYTHONPATH} | sed 's/:/ /g')
existed=0

for path in $python_paths
do
	if [ $advisor_path = $path ]; then
		existed=1
	fi
done

if [ $existed -eq 0 ]; then
	export PYTHONPATH=${PYTHONPATH}:${advisor_path}
fi
echo "PYTHONPATH=${PYTHONPATH}"

existed=0
for p in ${PATH}
do
    if [ "${advisor_path}/advisors" = $p ]; then 
        existed=1
    fi
done

if [ $existed -eq 0 ]; then
    export PATH=${PATH}:${advisor_path}/advisors:${advisor_path}/command
fi
echo "PATH=${PATH}"