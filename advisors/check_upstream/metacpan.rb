#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'
require './check_upstream/common'

def check_upstream_metacpan (prj_info)
	resp = ""
	info={}
	tags = ""
	cmd="curl -m 60 -s https://fastapi.metacpan.org/release/"+prj_info["src_repo"]
	resp = load_last_query_result(prj_info)
	if resp == ""
		begin
			retries  ||= 0
			resp=%x[#{cmd}]
			info=JSON.parse(resp) 
		rescue 
			STDERR.puts "DEBUG #{prj_info["src_repo"]} > No Respose or JSON parse failed\n"
			sleep 3
			retry if (retries += 1) < 10
		end
	else
		info = JSON.parse(resp)
	end
	if info != {} then
		if ! info.key?("version") then
			STDERR.puts "DEBUG #{prj_info["src_repo"]} > ERROR FOUND"
			return tags
		else
			tags = tags +info["version"].to_s+"\n"
		end
	else
		STDERR.puts "DEBUG #{prj_info["src_repo"]} > found unsorted on cpan.metacpan.org\n"
		return tags
	end
	last_query = {}
	last_query["time_stamp"] = Time.now
	last_query["raw_data"] = resp.dup
	prj_info["last_query"] = last_query
	return tags
end
