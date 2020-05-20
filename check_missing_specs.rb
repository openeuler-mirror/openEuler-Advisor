#!/usr/bin/ruby

require 'yaml'
require 'set'
require 'optparse'

require 'helper/download_spec'
require 'gitee/advisor'

options = {}
OptionParser.new do |opts|
	opts.barnner = "Usage: check_missing_spec.rb [options]"
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

specfile = download_spec(options[:repo])
if specfile == "" then
	puts "no spec file found for #{options[:repo]} project\n"
	if options[:push] then
		puts "Push this advise to gitee\n"
		ad = Advisor.new
		ad.new_issue("src-openeuler", options[:repo], 
			     "Submit spec file into this repository",
			     "Dear #{options[:repo]r}) maintainer:\n\n  We found there're no spec file in this repository yet.\n\n  Missing spec file implies that this components will not be integtaed into openEuler release, and your hardworking cannot help others.\n\n  We courage you submit your spec file into this repository as soon as possible.\n\n  This is a automatic advise from openEuler-Advisor. If you think the advise is not correct, please fill an issue at https://gitee.com/openeuler/openEuler-Advisor/ to help us improve.\n\n Yours openEuler Advisor.")
	else
		puts "Keep it between us\n"
	end
else
	puts "Everything's fine\n"
end


