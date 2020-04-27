#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'

def compare_tags (a, b)
	arr_a = a.split(".")
	arr_b = b.split(".")
	len = [arr_a.length, arr_b.length].min
	idx = 0
	while idx < len do
		res1 = arr_a[idx].to_i <=> arr_b[idx].to_i
		return res1 if res1 != 0
		res2 = arr_a[idx].length <=> arr_b[idx].length
		return -res2 if res2 != 0
		res3 = arr_a[idx][-1].to_i <=> arr_b[idx][-1].to_i
		return res3 if res3 != 0
		idx = idx + 1
	end
	return arr_a.length <=> arr_b.length
end

def clean_tag(tag, prj_info)
	if prj_info.has_key?("tag_pattern") then
		tag = tag.gsub(Regexp.new(prj_info["tag_pattern"]), "\\1")
	elsif prj_info.has_key?("tag_prefix") then
		tag = tag.gsub(Regexp.new(prj_info["tag_prefix"]), "")
	end
	if prj_info.has_key?("seperator") then
		tag = tag.gsub(prj_info["seperator"], ".")
	end
	return tag.gsub("\n", "")
end

def sort_tags (tags)
	tags.sort! { |a, b|
		compare_tags(a,b)
	}
	return tags
end

def upgrade_recommend(tags, cur_tag, policy)
	tags.reverse!
	tag1 = cur_tag
	tag2 = cur_tag
	if policy == "latest" then
		return tags[0]
	elsif policy == "latest-stable" then
		tags.each { |tag|
			if tag.split(".").count {|f| f.to_i != 0 } >= 3 then
				tag1 = tag
				break
			end
		}
		tags.each { |tag|
			if tag.split(".").count {|f| f.to_i != 0} >= 2 then
				tag2 = tag
				break
			end
		}
		if tag2[0].to_i > tag1[0].to_i then
			return tag2
		else
			return tag1
		end
	elsif policy == "perfer-stable" then
		tags.each { |tag|
			if tag.start_with?(cur_tag) then
				return tag
			end
		}
		if cur_tag.split(".").length >= 3 then
			search_tag = cur_tag.split(".")[0..1].join(".")
			tags.each { |tag|
				if tag.start_with?(search_tag) then
					return tag
				end
			}
		end
		return cur_tag
	else
		return cur_tag
	end

end

def load_last_query_result(prj_info, force_reload=false)
	if force_reload == true then
		prj_info.delete("last_query")
		STDERR.puts "DEBUG: #{prj_info["src_repo"].gsub("\n", "")} > Force Reload\n"
		return ""
	else
		if prj_info.has_key?("last_query") then
			last_query = prj_info["last_query"]
			if Time.now - last_query["time_stamp"] < 60*60*24*3 then
				STDERR.puts "DEBUG: #{prj_info["src_repo"].gsub("\n", "")} > Reuse Last Query\n"
				return last_query["raw_data"].dup
			else
				prj_info.delete("last_query")
				STDERR.puts "DEBUG: #{prj_info["src_repo"].gusb("\n", "")} > Last Query Too Old.\n"
				return ""
			end
		else
			return ""
		end
	end
end

def resp_to_git_tags(resp)
	tags = ""
	resp.each_line { |line|
		if line.match(/refs\/tags/) then
			match = line.scan(/^([^ \t]*)[ \t]*refs\/tags\/([^ \t]*)\n/)
			if match != nil then
				tags = tags + match[0][1].to_s + "\n"
			end
		end
	}
	return tags
end
