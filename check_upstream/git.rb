#!/usr/bin/ruby

require 'yaml'
require 'date'
require_relative 'common'

def check_upstream_git (prj_info)
	resp = load_last_query_result(prj_info)
	cmd="git ls-remote --tags "+prj_info["src_repo"]
	if resp == "" then
		resp=%x[#{cmd}]
		last_query={}
		last_query["time_stamp"] = Time.now
		last_query["raw_data"] = resp.dup
		prj_info["last_query"] = last_query
	end
	tags = resp_to_git_tags(resp)
	return tags
end

