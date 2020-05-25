#!/usr/bin/ruby
#
require 'yaml'
require 'set'
require 'optparse'


options = {}
OptionParser.new do |opts|
	opts.banner = "Usage: create_repo.rb [options]"
	opts.on("-y", "--repo REPO_YAML", "YAML file for repositories") do |n|
		puts "Adding repo to #{n}"
		options[:repo] = n
	end
	opts.on("-i", "--sigs SIGS_YAML", "YAML file for sigs") do |n|
		puts "Adding sig information to #{n}"
		options[:sigs] = n
	end
	opts.on("-s", "--sig SIG", "Sig manage this repo") do |n|
		puts "Repo managed by #{n}"
		options[:sig] = n
	end
	opts.on("-n", "--name NAME", "Name for new repo") do |n|
		puts "Adding #{n} new repo"
		options[:name] = n
	end
	opts.on("-d", "--description DESC", "Description for new repo") do |n|
		puts "New repo is for #{n}"
	      	options[:desc] =n 	
	end
	opts.on("-u", "--upstream UP", "Upstream for new repo") do |n|
		puts "Upstream is #{n}"
		options[:upstream] = n
	end
	opts.on("-h", "--help", "Print help") do
		puts opts
		exit
	end
end.parse!

if not (options[:upstream] and options[:desc] and options[:name] and options[:sigs] and options[:sig] and options[:repo] ) then
	puts "Missing parameter"
	puts "-h to get help"
	exit 1
end

sigs = YAML.load(File.read(options[:sigs]))
repo = YAML.load(File.read(options[:repo]))

nr = Hash.new
nr["name"] = options[:name]
nr["description"] = options[:desc]
nr["upstream"] = options[:upstream]
nr["protected_branches"] = ["master"]
nr["type"] = "public"

if repo["community"] == "openeuler" then
	repo["repositories"].push(nr)
elsif repo["community"] == "src-openeuler" then
	nr["upstream"] = options[:upstream]
	repo["repositories"].push(nr)
end

repo["repositories"].sort_by! { |r| r["name"] }

sigs["sigs"].each { |s|
	if s["name"] == options[:sig] then
		s["repositories"].push("#{repo["community"]}/#{options[:name]}")
		next
	end
}

File.open(options[:repo], "w") {|file| file.write(repo.to_yaml)}
File.open(options[:sigs], "w") {|file| file.write(sigs.to_yaml)}
