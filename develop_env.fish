#!/usr/bin/env bash
#Config environment before develop, please run: source ./develop_env.sh

set -e fish_trace
set advisor_path (cd (dirname (status -f)); and pwd)

set existed 0
for p in $PYTHONPATH
	if [ $advisor_path = $p ]
		set existed 1
		break
	end
end

if [ $existed -eq 0 ]
	set -x PYTHONPATH $PYTHONPATH $advisor_path
end
echo "PYTHONPATH=$PYTHONPATH"

set existed 0
for p in $PATH
	if [ "$advisor_path/advisors" = $p ]
		set existed 1
		break
	end
end
if [ $existed -eq 0 ]
	set -x PATH $PATH $advisor_path/advisors $advisor_path/command
end
echo "PATH=$PATH"
	
