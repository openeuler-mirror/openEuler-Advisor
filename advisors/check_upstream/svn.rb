#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'
require_relative 'common'

def check_upstream_svn (prj_info)
	cmd="/usr/bin/svn ls -v "+prj_info["src_repo"]+"/tags"
	resp = load_last_query_result(prj_info)
	if resp == "" then
		resp = %x[#{cmd}]
		last_query = {}
		last_query["time_stamp"] = Time.now
		last_query["raw_data"] = resp.dup
		prj_info["last_query"] = last_query
	else
	end
	sorted_tags = []
	resp.each_line { |tag_line|
		match = tag_line.scan(/([.\w]+)/)
		if match != nil then
			if match[5][0].include?(prj_info["tag_prefix"]) then
				new_tag = Hash.new
				new_tag["Date"] = Date.parse(match[2][0]+" "+match[3][0]+" "+match[4][0])
				tag = match[5][0]
				new_tag["Tag"] = tag.gsub(prj_info["tag_prefix"], "").gsub(prj_info["seperator"], ".")
				sorted_tags.append(new_tag)
			end
		end
	}
	sorted_tags.sort_by! {|t| t["Date"] }
	result = []
	sorted_tags.each { |t|
		result.append(t["Tag"])
	}
	return result
end

