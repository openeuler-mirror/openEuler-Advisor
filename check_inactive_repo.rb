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
		     "Dear #{options[:repo]} developer:\n亲爱的 #{options[:repo]} 开发者：\n\n  We found this repository has not fulfill what it prupose to be.\n我们发现这个代码仓并没有承载它被期望的功能。\n\n  Long time no progress will discourge other developers to follow and participant this initiative.\n长期没有代码会使得关注这个项目的开发者失望。\n\n  Please start submit something as soon as possible.\n建议您尽快向代码仓提交进展。\n\n  This is a automatic advise from openEuler-Advisor. If you think the advise is not correct, please fill an issue at https\:\/\/gitee.com\/openeuler\/openEuler-Advisor to help us improve.\n这是一条由 openEuler-Advisor 自动生成的建议。如果您认为这个建议不对，请访问 https\:\/\/gitee.com\/openeuler\/openEuler-Advisor 来帮助我们改进。\n\n Yours openEuler Advisor.")
end
