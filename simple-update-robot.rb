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

def update_spec(file, over, nver)
	f = File.read(file)
	fn = File.open(file+".new", "w")
	f.each_line { |l|
		if l.match(/^Release/) then
			fn.puts "Release:	0"
			next
		end
		nl = l.gsub(over, nver)
		fn.write(nl)
		if nl.match(/%changelog/) then
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

source.each { |s|
	ns = s.gsub(Old_ver, New_ver)
	fn = File.basename(ns)
	cmd = "curl -L " + ns + " -o " + fn
	puts cmd
	%x[#{cmd}]
}

update_spec(specfile, Old_ver, New_ver)
