#!/usr/bin/env bash
#Config environment before develop, please run: source ./develop_env.sh

set -e fish_trace
set advisor_path (cd (dirname (status -f)); and pwd)

set existed 0
for path in $PYTHONPATH
	if [ $advisor_path = $path ]
		set existed 1
		break
	end
end

if [ $existed -eq 0 ]
	set -x PYTHONPATH $PYTHONPATH $advisor_path
end
echo "PYTHONPATH=$PYTHONPATH"
