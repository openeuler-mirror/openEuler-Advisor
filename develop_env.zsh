#!/bin/zsh
#Config environment before develop, please run: source ./develop_env.zsh

advisor_path=$(cd $(dirname $funcstack[1]); pwd)
python_paths=$(echo ${PYTHONPATH} | sed 's/:/ /g')
existed=0

for p in $python_paths
do
	if [ $advisor_path = $p ]; then
		existed=1
	fi
done

if [ $existed -eq 0 ]; then
	export PYTHONPATH=${PYTHONPATH}:${advisor_path}
fi
echo "PYTHONPATH=${PYTHONPATH}"


existed=0
for p in $fpath
do
    if [ "${advisor_path}/advisors" = $p ]; then 
        existed=1
    fi
done

if [ $existed -eq 0 ]; then
    fpath+=("${advisor_path}/advisors" "${advisor_path}/command")
    export PATH=${PATH}:${advisor_path}/advisors:${advisor_path}/command

fi
echo "PATH=${PATH}"
