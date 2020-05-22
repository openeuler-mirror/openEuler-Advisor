#!/usr/bin/ruby
# process
# 1. get URL to download updated version
#    so far we know the URL in spec is not reliable
# 2. Change Version to new one
# 3. Change Source or Source0 if needed
# 4. Update %changelog
# 5. try rpmbuild -bb
# 6. fork on gitee
# 7. git clone, git add, git commit, git push
# 8. PR on gitee

require 'date'
require "./helper/download_spec.rb"
require "./helper/rpmparser.rb"
require 'yaml'

if not ARGV[0] then
	puts "Missing repo name"
	exit 1
end

Old_ver = ARGV[1]
New_ver = ARGV[2]
specfile = download_spec(ARGV[0])

spec = Specfile.new (specfile)

source = spec.get_sources
if source.length > 1 then
	puts "I'm too Naive to handle complicated package"
	exit 1
end

source = spec.expand_macros(source)

def update_spec(file, over, nver, src_fn=false)
	f = File.read(file)
	fn = File.open(file+".new", "w")
	in_changelog = false
	f.each_line { |l|
		if l.match(/^Release/) then
			fn.puts "Release:	0"
			next
		end
		if l.match(/^Source/) then
			if src_fn then
				fn.puts "Source:	#{src_fn}"
			else
				fn.puts l
			end
			next
		end
		if not in_changelog then
			nl = l.gsub(over, nver)
		else
			nl = l
		end
		fn.puts nl
		if nl.match(/%changelog/) then
			in_changelog = true
			d = DateTime.now
			fn.puts d.strftime("* %a %b %d %Y SimpleUpdate Robot <tc@openeuler.org>")
			fn.puts "- Update to version #{ARGV[2]}"
			fn.puts ""
		end
	}
	fn.close
	File.rename(file,file+".old")
	File.rename(file+".new", file)
end

def try_spec_url(src, over, nver)
	src.each { |s|
		ns = s.gsub(over, nver)
		if ns.match(/%{.*?}/) then
			    STDERR.puts "Extra macros in URL which I cannot expand"
			    return false
		elsif ns.match(/^http/) or ns.match(/^ftp/) then
			fn = File.basename(ns)
			cmd = "curl -L " + ns + " -o " + fn
			puts cmd
			%x[#{cmd}]
			return fn
		else
			return false
		end
	}
end

def try_upstream_url(repo, over, nver)
	upstream_yaml = "upstream-info/"+repo+".yaml"
	if not File.exist?(upstream_yaml) then
		STDERR.puts "No upstream info found for this package"
		return false
	end
	rp_yaml = YAML.load(File.read(upstream_yaml))
	if rp_yaml["version_control"] == "github" then
		cmd = "curl -L https://github.com/#{rp_yaml["src_repo"]}/archive/#{nver}.tar.gz -o #{repo}.#{nver}.tar.gz"	
		%x[#{cmd}]
		return "#{repo}.#{nver}.tar.gz"
	else
		STDERR.puts "Handling #{version_control} is still under developing"
		return false
	end

end

src_fn = try_spec_url(source, Old_ver, New_ver)
if src_fn then
	update_spec(specfile, Old_ver, New_ver)
else
	src_fn = try_upstream_url(ARGV[0], Old_ver, New_ver)
	if src_fn then
		update_spec(specfile, Old_ver, New_ver, src_fn)
	else
		STDERR.puts "Cannot find the source code for upgrading"
		exit 1
	end
end

