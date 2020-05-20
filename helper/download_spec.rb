#!/usr/bin/ruby

require 'yaml'

def download_spec(name)
	output_dir = "."
	exception_load = YAML.load(File.read(File.dirname(__FILE__)+"/specfile_exceptions.yaml"))
	if exception_load.has_key?(name) then
		output_file = "#{output_dir}/#{exception_load[name]["file"]}"
		cmd = "curl -s https://gitee.com/src-openeuler/#{name}/raw/master/#{exception_load[name]["dir"]}/#{exception_load[name]["file"]} -o #{output_file}"
	else
		output_file = "#{output_dir}/#{name}.spec"
		cmd = "curl -s https://gitee.com/src-openeuler/#{name}/raw/master/#{name}.spec -o #{output_file}"

	end
	%x[#{cmd}] if ! File.exists?(output_file)
	s = File.size(output_file)
	if s == 52 then
		sig = search_sig(sigs, name)
		STDERR.puts "> No SPEC file found for #{name}, which managed by #{sig}"
		File.delete output_file
		return ""
	end
	return output_file
end

