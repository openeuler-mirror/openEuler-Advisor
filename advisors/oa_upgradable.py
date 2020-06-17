#!/usr/bin/python3

from pyrpm.spec import Spec, replace_macros

import yaml
import json
import datetime
import sys
import os
import argparse

import urllib.error
import gitee
import check_upstream
import version_recommend

if __name__ == "__main__":
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-p", "--push", action="store_true",
            help="Push the version bump as an issue to src-openeuler repository") 
    parameters.add_argument("-d", "--default", type=str, default=os.getcwd(),
            help="The fallback place to look for YAML information")
    parameters.add_argument("repo", type=str,
            help="Repository to be checked for upstream version info") 

    args = parameters.parse_args()

    gitee = gitee.Gitee()
    prj_name = args.repo
    spec_string = gitee.get_spec(prj_name)
    s_spec = Spec.from_string(spec_string)

    current_version = s_spec.version

    print(prj_name)
    print(current_version)

    try:
        prj_info_string = gitee.get_yaml(prj_name)
    except urllib.error.HTTPError:
        prj_info_string = ""

    if not prj_info_string:
        print("Fallback to {dir}".format(dir=args.default))
        prj_info_string = open(os.path.join(args.default, prj_name + ".yaml")).read()

    if not prj_info_string:
        print("Failed to get YAML info for {pkg}".format(pkg=prj_name))
        sys.exit(1)

    prj_info = yaml.load(prj_info_string, Loader=yaml.Loader)

    vc_type = prj_info["version_control"]
    if vc_type == "hg":
        tags = check_upstream.check_hg(prj_info)
    elif vc_type == "github":
        tags = check_upstream.check_github(prj_info)
    else:
        pass

    print("tags :", tags)
    v = version_recommend.VersionRecommend(tags, current_version, 0)
    print("Latest version is ", v.latest_version)
    print("Maintain version is", v.maintain_version)
"""
    if vc_type == "svn":
        tags = check_upstream_svn(prj_info)
    elif vc_type == "git":
        tags = check_upstream_git(prj_info)
	tags = clean_tags(tags.lines)
    elif vc_type == "metacpan":
	tags = check_upstream_metacpan(prj_info)
	tags = clean_tags(tags.lines)
    elif vc_type == "gitlab.gnome":
	tags = check_upstream_gnome(prj_info)
	tags = clean_tags(tags.lines)
    elif vc_type == "pypi":
	tags = check_upstream_pypi(prj_info)
	tags = clean_tags(tags.lines)
    else:
        print("Unsupport version control method {vc}".format(vc=vc_type))
        sys.exit(1)
"""
"""
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
"""
