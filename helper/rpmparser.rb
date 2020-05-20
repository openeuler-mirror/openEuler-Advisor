#!/usr/bin/ruby 

require 'yaml'
require 'set'

def rpmspec_split_tags (line, prefix)
    m = line.scan (/#{prefix}\s*(.*)/)
    if m != [] then
	    br = m[0][0]
	    if br.index(',') then
		    bra = br.split(',').map(&:strip)
		    return bra
	    elsif br =~ /\w\s+\w/ then
		    bra = br.split(/\s+/)
		    return bra
        end
    end
    return nil
end

def rpmspec_clean_tag (oset, mac)

    new_set = Set.new

    oset.each { |br|
        if br[0] =~ /[\d<=>!]/ then
            oset.delete(br)
        elsif br =~ /[<=>!]/ then
            bra = br.split("\s").map(&:strip)
            oset.delete(br)
            new_set << bra[0]
        elsif br.match(/%{/) then
            m = br.scan(/%{(.*?)}/)
            if m != [] then
                nbr = br.gsub(/%{#{m[0][0]}}/, mac[m[0][0]])
                oset.delete(br)
                new_set << nbr
            end
        end
    }
    oset += new_set
    return oset
end


class Specfile
	def initialize(filepath)
		spec = File.open("#{filepath}")
		@macros = {}
		@macros["epoch"] = "1"
		@name = ""
		@version = ""
		@release = ""

		@build_requires = Set.new
		@requires = Set.new
		@provides = Set.new

		spec.each_line { |line| 
			m = line.scan (/^[Nn]ame\s*:\s*([^\s]*)\s*/)
			if m != [] then
				@name = m[0][0]
			end
			m = line.scan (/^[Vv]ersion\s*:\s*([^\s]*)\s*/)
			if m != [] then
				@version = m[0][0]
			end
			m = line.scan (/^[Rr]elease\s*:\s*([^\s]*)\s*/)
			if m != [] then
				@release = m[0][0]
			end
			m = line.scan (/%global\s*([^\s]*)\s*(.*)/)
			if m != [] then
				@macros[m[0][0]] = m[0][1]
			end
			m = line.scan (/%define\s*([^\s]*)\s*(.*)/)
			if m != [] then
				@macros[m[0][0]] = m[0][1]
			end
			bra = rpmspec_split_tags(line, "BuildRequires:")
			if bra != nil then
				@build_requires += bra
			end
			ra = rpmspec_split_tags(line, "Requires:")
			if ra != nil then
				@requires += ra
			end
			po = rpmspec_split_tags(line, "Provides:")
			if po != nil then
				@provides += po
			end
		}
		if @name.match(/%{/) then
			m = @name.scan(/%{(.*)}/)
			if m != [] then
				@name = @name.gsub(/%{#{m[0][0]}}/, @macros[m[0][0]])
			end
		end
		@macros["name"] = @name

		if @version.match(/%{/) then
			m = @version.scan(/%{(.*)}/)
			if m != [] then
				@version = @version.gsub(/%{#{m[0][0]}}/, @macros[m[0][0]])
			end
		end
		@macros["version"] = @version

		if @release.match(/%{/) then
			m = @release.scan(/%{(.*)}/)
			if m != [] then
				@release = @release.gsub(/%{#{m[0][0]}}/, @macros[m[0][0]])
			end
		end
		@macros["release"] = @release

		@build_requires = rpmspec_clean_tag(@build_requires, @macros)
		@requires = rpmspec_clean_tag(@requires, @macros)
		@provides = rpmspec_clean_tag(@provides, @macros)
	end

	def get_name
		return @name
	end

	def get_version
		return @version
	end
#newspec = {}
#newspec["name"] = name
#newspec["release"] = release
#newspec["version"] = version
#newspec["build_requires"] = build_requires
#newspec["provides"] = provides
#newspec["requires"] = requires

end

