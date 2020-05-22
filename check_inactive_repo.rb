#!/usr/bin/ruby

require 'yaml'
require 'set'
require 'optparse'

require './helper/download_spec'
require './gitee/advisor'

INACTIVE_THRESHOLD = 3

options = {}
OptionParser.new do |opts|
	opts.banner = "Usage: check_inactive_repo.rb [options]"
	opts.on("-p", "--push", "Push the advise to gitee.com/openeuler") do |v|
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

cmd = "git ls-remote https://gitee.com/openeuler/#{options[:repo]}/"
refs = %x[#{cmd}]
merge_count = 0
refs.each_line { |line|
	if line.match(/\/pull\/(\d*)\/MERGE/) then
		merge_count = merge_count + 1
	end
	puts line
}
puts merge_count
if merge_count < INACTIVE_THRESHOLD then
	ad = Advisor.new
	ad.new_issue("openeuler", options[:repo],
		     "Inactive repository",
		     "Dear #{options[:repo]} developer:\n\n  We found this repository has not fulfill what it prupose to be.\n\n  Long time no progress will discourge other developers to follow and participant this initiative.\n\n  Please start submit something as soon as possible.\n\n")
end
