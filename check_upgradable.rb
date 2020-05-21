#!/usr/bin/ruby

require 'yaml'
require 'json'
require 'date'
require 'optparse'

require './check_upstream/github'
require './check_upstream/git'
require './check_upstream/hg'
require './check_upstream/svn'
require './check_upstream/metacpan'
require './check_upstream/gnome'
require './check_upstream/pypi'
require './helper/download_spec'
require './helper/rpmparser'
require './gitee/advisor'

options = {}

OptionParser.new do |opts|
	opts.banner = "Usage: check_upgradable.rb [options]"
	opts.on("-p", "--push", "Push the advise to gitee.com/src-openeuler") do |v|
		options[:push] = v
	end
	opts.on("-r", "--repo REPO_NAME", "Repo to check upstream info") do |n|
		puts "Checking #{n}"
		options[:repo] = n
	end
	opts.on("-h", "--help", "Prints this help") do
		puts opts
		exit
	end
end.parse!

if not options[:repo] then
	puts "Missing repo name\n"
	exit 1
end 

Prj_name = options[:repo]
specfile=download_spec(Prj_name)
if specfile == "" then
	puts "no specfile found for project\n"
	exit 1
end
spec_struct = Specfile.new(specfile)
Cur_ver = spec_struct.get_version

Prj_info = YAML.load(File.read "upstream-info/"+Prj_name+".yaml")

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

def sort_tags (tags)
	tags.sort! { |a, b|
		compare_tags(a,b)
	}
	return tags
end

def clean_tags(tags)
	new_tags = []
	tags.each{|line|
		new_tags = new_tags.append clean_tag(line, Prj_info)
	}
	return new_tags
end

def upgrade_recommend(tags_param, cur_tag, policy)
	tags = tags_param.reverse
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

print Prj_name, ":\n"

if Prj_info["version_control"] == "svn" then
	tags = check_upstream_svn(Prj_info)
elsif Prj_info["version_control"] == "github" then
	tags = check_upstream_github_by_api(Prj_info)
	if tags == nil or tags == "" then
		tags = check_upstream_github_by_git(Prj_info)
	end
	tags = clean_tags(tags.lines)
elsif Prj_info["version_control"] == "git" then
	tags = check_upstream_git(Prj_info)
	tags = clean_tags(tags.lines)
elsif Prj_info["version_control"] == "hg" then
	tags = check_upstream_hg(Prj_info)
	tags = clean_tags(tags.lines)
elsif Prj_info["version_control"] == "metacpan" then
	tags = check_upstream_metacpan(Prj_info)
	tags = clean_tags(tags.lines)
elsif Prj_info["version_control"] == "gitlab.gnome" then
	tags = check_upstream_gnome(Prj_info)
	tags = clean_tags(tags.lines)
elsif Prj_info["version_control"] == "pypi" then
	tags = check_upstream_pypi(Prj_info)
	tags = clean_tags(tags.lines)
end

tags = sort_tags(tags)
print "Latest upstream is ", tags[-1], "\n"
#print "Recommended is     ", upgrade_recommend(tags, Cur_ver, "latest-stable"), "\n"
print "Current version is ", Cur_ver, "\n"

puts "This package has #{spec_struct.get_diverse} patches"

if tags.length == 0 or compare_tags(tags[-1], Cur_ver) < 0 then
	STDERR.puts "DEBUG #{Prj_name} > tags are #{tags}"
	File.delete("upstream-info/"+Prj_name+".yaml") if File.exist?("upstream-info/"+Prj_name+".yaml")
	File.open("known-issues/"+Prj_name+".yaml", "w") { |file| file.write(Prj_info.to_yaml) }
else
	File.open("upstream-info/"+Prj_name+".yaml", "w") { |file| file.write(Prj_info.to_yaml) }
end
File.delete(specfile) if specfile != ""

if options[:push] then
	puts "Push to gitee\n"
	ad = Advisor.new
	ad.new_issue("src-openeuler", Prj_name, "Upgrade to Latest Release", "Dear #{Prj_name} maintainer:\n\n  We found the latst version of #{Prj_name} is #{tags[-1]}, while the current version in openEuler is #{Cur_ver}.\n\n  Please consider upgrading.\n\n\nYours openEuler Advisor.")
else
	puts "keep it to us\n"
end
