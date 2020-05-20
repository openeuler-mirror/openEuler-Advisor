#!/usr/bin/ruby

require 'json'

class Advisor
	def initialize
		@token = JSON.parse(File.read (File.expand_path "~/.gitee_token.json"))
		@cmd = "curl -X POST --header 'Content-Type: application/json;charset=UTF-8'"
		@param = {}
	end

	def new_issue(owner, repo, title, body)
		@param["access_token"] = @token["access_token"]
		@param["repo"] = repo
		@param["title"] = title
		@param["body"] = body
		@cmd += " 'https://gitee.com/api/v5/repos/#{owner}/issues'"
		@cmd += " -d '" + @param.to_json + "'"
		#puts @cmd
		resp = %x[#{@cmd}]
		#puts resp
	end
end

#ad = Advisor.new
#ad.new_issue("Shinwell_Hu", "openEuler-Toolbox")
