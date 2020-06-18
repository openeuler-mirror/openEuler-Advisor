#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'
require './check_upstream/common.rb'

def check_upstream_pypi (prj_info)
	resp = ""
	info={}
	tags = ""
	resp = load_last_query_result(prj_info)
	if resp == "" then
		last_query={}
		last_query["time_stamp"] = Time.now
		cmd="curl -m 60 -s -L https://pypi.org/pypi/"+prj_info["src_repo"]+"/json"
		begin
			retries ||= 0
			resp=%x[#{cmd}] 
			info=JSON.parse(resp) 
		rescue 
			STDERR.puts "DEBUG: #{prj_info["src_repo"].gsub("\n", "")} > No Respose or JSON parse failed\n"
			sleep 3
			retry if (retries+=1)<10
		end
		if info != {} then
			last_query["raw_data"] = resp
			prj_info["last_query"] = last_query
		end
	else
		info=JSON.parse(resp)
	end
	if info != {} then
		tags = tags + info["info"]["version"].to_s+"\n"
	end
	return tags
end
