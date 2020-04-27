#!/usr/bin/ruby

require 'yaml'
require 'date'
require_relative 'common'

def check_upstream_hg (prj_info)
	cookie = ""
	cmd="curl -s "+prj_info["src_repo"]+"/raw-tags"
	resp = load_last_query_result(prj_info)
	if resp == "" then
		resp = %x[#{cmd}]
		if resp.lines[0].match(/html/) then # we got html response, resend with cookie
			resp.each_line { |line|
				match = line.scan(/document\.cookie=\"(.*)\";/)
				if match != [] then
					cookie = cookie + match[0][0]
				end
			}
			cmd="curl -s --cookie \""+cookie+"\" "+prj_info["src_repo"]+"/raw-tags"
			resp = %x[#{cmd}]
		end
		last_query={}
		last_query["time_stamp"] = Time.now
		last_query["raw_data"] = resp.dup
		prj_info["last_query"] = last_query
	end
	tags = ""
	resp.each_line { |line|
		if line.match(/^tip/) then
			next
		end
		match = line.scan(/^([\w\d\-\.]*)[ \t]*([\w\d\-\.]*)/)
		if match != [] then
			tags = tags + match[0][0].to_s + "\n"
		end
	}
	return tags
end
