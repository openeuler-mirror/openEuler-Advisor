## openEuler-Advisor

### Description
Collection of automation tools for easily maintaining openEuler

| Pharse           | Rules           | Requires  | Automatic  | Data & Tool   |
|------------------|-----------------------|---|---|------|
| 1.Select & Fetch | 1.1 Official Release  | official git/svn.. url  | from spec, from other package system  | [Software Metadata](#Software-Metadata) |
|                  | 1.2 Best Version     | release note、test、user feedback   | newest/stable/official/compatible version  |      |
|                  | 1.3 Best Version Notify | issue/PR | auto issue/PR | |
| 2.Package        | 2.1 Meta data | summary, deps ...  |  from spec, from other package system    |    |
|                  | 2.2 Check Old Patch (while updating) | drop upstreamed patch; check conflict  |   | 
|                  | 2.3 Python to RPM  | way to build python package by pip | turn pip to rpm |   |       
| 3.Modify         | 3.1 CVE & CVE official fix | CVE notify & official patch/commit  |   |      
|                  | 3.2 Patch upstream    | upstream bugzilla/git URL | auto bugzilla/PR  |      |
| 4.Test           | 4.1 Upstream Test & Feedback   | upstream test entry & feedback channel  | standard test entry & auto feedback  |  |
| 5.Release        | TODO       |   |   |   


### Software Metadata
#### Configs
```
version_control: git
src_repo: xxxx
tag_prefix: ^v
separator: .
```

**version_control**
The type of a software's version control system.
Now we support:  `svn/github/git/hg/metacpan/gitlab.gnome/pypi`

**src_repo**
The original official source url of a software.

**tag_prefix**
The version name is not always the same with the tag name. 
For example, if a software version is 1.0.0, the tag might be v1.0.0. `v` here is the prefix.

**separator**
The separator of a software's version name. For example, if a software version is 1.0.0, the separator is `.`.

#### How to add a software metadata file
0. Please check if the metafile is already exist
1. Copy the [Template](./template.yaml) to [Database Dir](./upstream-info)
2. Rename the file name, it is suggested that the file name SHOULD be same with the repo name in `src-openeuler`.
3. Find the official source url of the software.
4. Check the version control type, the tag prefix and the separator
5. Fill the configs

DONE! than you can create a Pull Request.

#### Metadata Database
[Database](./upstream-info)  
	
	
#### Enviroment Setting
##### 1. necessary packages install
	pip3 install python-rpm-spec (ver:0.9)
	pip3 install PyYAML (ver:5.3.1)
	
##### 2. json file config
	~/.gitee_personal_token.json
	content format: {"user":"user_name","access_token":"token_passwd"}
	
	setting personal access token: https://gitee.com/profile/personal_access_tokens
	
#### Use Instructions
##### 1. simple-update-root.py
	single package auto-upgrade: python3 simple-update-root.py -u pkg pkg_name branch_name
	ep: python3 simple-update-root.py -u pkg snappy master

	single package manual upgrade: python3 simple-update-root.py pkg_name branch_name [-fc] [-d] [-s] [-n new_version] [-p]
	ep: python3 simple-update-root.py snappy openEuler-20.03-LTS -fc -d -s -n 1.8.1
	
	multi-packages in a repo auto-upgrade: python3 simple-update-root.py -u repo repo_name branch_name
	ep: python3 simple-update-root.py -u repo src_openEuler master
	
##### 2. oa_upgradable.py 
	display all tags of target package: python3 oa_upgradable.py pkg_name
	ep: python3 oa_upgradable.py glibc
	
#### Consultation for advisor:
	if any problem, please contact: leo.fangyufa@huawei.com/leofang_94@163.com
	
	
### Contribution

1.  Fork the repository
2.  Create Feat_xxx branch
3.  Commit your code
4.  Create Pull Request

