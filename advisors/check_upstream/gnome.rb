#!/usr/bin/ruby

require 'yaml'
require 'date'
require_relative 'common'

def check_upstream_gnome (prj_info)
	resp = ""
	resp = load_last_query_result(prj_info)
	if resp == "" then
		cmd="git ls-remote --tags https://gitlab.gnome.org/GNOME/"+prj_info["src_repo"]+".git"
		resp = %x[#{cmd}]
		last_query={}
		last_query["time_stamp"] = Time.now
		last_query["raw_data"] = resp.dup
		prj_info["last_query"] = last_query
	end
	tags = resp_to_git_tags(resp)
	return tags
end

