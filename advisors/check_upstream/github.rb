#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'
require_relative 'common'

def check_upstream_github_by_api (prj_info)
	cmd="/usr/bin/curl -m 60 -s https://api.github.com/repos/"+prj_info["src_repo"]+"/releases"
	resp = load_last_query_result(prj_info)
	if resp == "" then
		STDERR.puts "DEBUG #{prj_info["src_repo"]} > Using api.github to get releases"
		begin
			retries ||= 0
			resp=%x[#{cmd}]
			release = JSON.parse(resp)
		rescue
			STDERR.puts "DEBUG #{prj_info["src_repo"]} > No Response or JSON Parse failed. Retry in 3 seconds.\n"
			sleep 3
			retry if (retries+=1) < 10
		end
		if release != [] and release != nil then
			last_query = {}
			last_query["time_stamp"] = Time.now
			last_query["raw_data"] = resp.dup
			prj_info["last_query"] = last_query
			prj_info["query_type"] = "api.github.releases"
		else
			# fall back to tags
			STDERR.puts "DEBUG #{prj_info["src_repo"]} > Using api.github to get tags"
			resp=""
			cmd="/usr/bin/curl -m 60 -s https://api.github.com/repos/"+prj_info["src_repo"]+"/tags"
			tags=[]
			begin
				retries ||= 0
				resp=%x[#{cmd}]
				tags=JSON.parse(resp)
			rescue
				STDERR.puts "DEBUG #{prj_info["src_repo"]} > No Response or JSON Parse failed. Retry in 3 seconds.\n"
				sleep 3
				retry if (retries += 1) < 10
			end
			if tags == [] or tags == nil then
				print "WARNING: #{prj_info["src_repo"]}'s upstream version not available~"
				return ""
			else
				last_query = {}
				last_query["time_stamp"] = Time.now
				last_query["raw_data"] = resp.dup
				prj_info["last_query"] = last_query
				prj_info["query_type"] = "api.github.tags"
			end
		end
	end

	if prj_info["query_type"] == "api.github.releases" then
		result = ""
		begin
			release = JSON.parse(resp)
			release.sort_by! { |e| e["created_at"]}
			release.each { |r|
				result = result + clean_tag(r["tag_name"], prj_info) + "\n"
			}
		rescue
		end
		return result
	elsif prj_info["query_type"] == "api.github.tags" then
		result = ""
		begin
			tags = JSON.parse(resp)
			tags.each { |r|
				result = result + clean_tag(r["name"], prj_info) + "\n"
			}
		rescue
		end
		return result
	else
		return ""
	end
end

def check_upstream_github_by_git(prj_info)
	resp = load_last_query_result(prj_info)
	if prj_info.has_key?("query_type") and prj_info["query_type"] != "git-ls" then
		resp = ""
	end
	cmd="git ls-remote --tags https://github.com/"+prj_info["src_repo"]+".git"
	if resp == "" then
		STDERR.puts "DEBUG #{prj_info["src_repo"]} > Using git ls-remote"
		resp=%x[#{cmd}]
		last_query = {}
		last_query["time_stamp"] = Time.now
		last_query["raw_data"] = resp.dup
		prj_info["last_query"] = last_query
		prj_info["query_type"] = "git-ls"
	end
	tags = resp_to_git_tags(resp)
	return tags
end

