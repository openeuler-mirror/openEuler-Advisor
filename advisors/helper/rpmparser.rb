#!/usr/bin/ruby 

require 'yaml'
require 'set'

def rpmspec_split_file (line, prefix)
    m = line.scan (/#{prefix}\s*(.*)/)
    if m != [] then
	    return m[0][0]
    else
	    return nil
    end
end

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
	    i = 0
	    nbr = br
	    while i < m.length do
		    if mac[m[i][0]] then
			    nbr = nbr.gsub(/%{#{m[i][0]}}/, mac[m[i][0]])
		    else
			    # some strange RPM macro needs shell expand, I dont know ohw to handle this
		    end
		    i = i + 1
	    end
	    oset.delete(br)
	    new_set << nbr
        end
    }
    oset += new_set
    return oset
end

def rpmspec_macro_expand(tag, macro)
	##This needs a fix
	if tag.match(/%{/) then
		m = tag.scan(/%{(.*)}/)
		if m != [] then
			if macro[m[0][0]] then
				tag = tag.gsub(/%{#{m[0][0]}}/, macro[m[0][0]])
			end
		end
	end
	return tag
end

class Specfile
	def initialize(filepath)
		spec = File.open("#{filepath}")
		@macros = {}
		@macros["epoch"] = "1"
		@macros["?_isa"] = "aarch64"
		@name = ""
		@version = ""
		@release = ""

		@build_requires = Set.new
		@requires = Set.new
		@provides = Set.new

		@sources = Set.new
		@patches = Set.new

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
			src = rpmspec_split_file(line, "Source\\d*:")
			if src != nil then
				@sources << src
			end
			pa = rpmspec_split_file(line, "Patch\\d*:")
			if pa != nil then
				@patches << pa
			end
		}
		@name = rpmspec_macro_expand(@name, @macros)
		@macros["name"] = @name

		@version = rpmspec_macro_expand(@version, @macros)
		@macros["version"] = @version

		@release = rpmspec_macro_expand(@release, @macros)
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

	def get_diverse
		return @patches.length
	end

	def get_sources
		return @sources
	end

	def expand_macros(s)
		return rpmspec_clean_tag(s, @macros)
	end
#newspec = {}
#newspec["name"] = name
#newspec["release"] = release
#newspec["version"] = version
#newspec["build_requires"] = build_requires
#newspec["provides"] = provides
#newspec["requires"] = requires

end

