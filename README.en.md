# openEuler-Advisor

## Description
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


## Software Metadata
### Configs
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

### How to add a software metadata file
0. Please check if the metafile is already exist
1. Copy the [Template](./template.yaml) to [Database Dir](./upstream-info)
2. Rename the file name, it is suggested that the file name SHOULD be same with the repo name in `src-openeuler`.
3. Find the official source url of the software.
4. Check the version control type, the tag prefix and the separator
5. Fill the configs

DONE! than you can create a Pull Request.

### Metadata Database
[Database](./upstream-info)  
	
### Introduction of advisors 	
#### Enviroment Setting
##### 1. necessary packages install
	pip3 install python-rpm-spec (ver>=0.10)
	pip3 install PyYAML (ver>=5.3.1)
	pip3 install requests (ver>=2.24.0)
	yum install rpmdevtools (ver>=8.3)
	pip3 install beautifulsoup4 (ver>=4.9.3)
	
##### 2. json file config
	~/.gitee_personal_token.json
	content format: {"user":"user_name","access_token":"token_passwd"}
	
	setting personal access token: https://gitee.com/profile/personal_access_tokens

##### 3. gitee ssh config
	if not config, please refer: https://gitee.com/help/articles/4181

##### 4. OBS config
	if not config, please refer: https://openeuler.org/zh/docs/20.09/docs/ApplicationDev/%E6%9E%84%E5%BB%BARPM%E5%8C%85.html

##### 5. Python enviroment config
	if in development, you want to use the tool directly, please config Python path firstly: source ./develop_env.sh

#### Use Instructions
##### 1. simple_update_robot.py
	single package auto-upgrade: python3 simple_update_robot.py -u pkg pkg_name branch_name
	ep: python3 simple_update_robot.py -u pkg snappy master

	single package manual upgrade: python3 simple_update_robot.py pkg_name branch_name [-fc] [-d] [-s] [-n new_version] [-b] [-p]
	ep: python3 simple_update_robot.py snappy openEuler-20.03-LTS -fc -d -s -n 1.8.1
	
	multi-packages in a repo auto-upgrade: python3 simple_update_robot.py -u repo repo_name branch_name
	ep: python3 simple_update_robot.py -u repo src-openeuler master

	you can config local yaml for auto upgrade, such as: upgrade-example.yaml
	repositories:
	- name: A-Tune
	- name: python-py
	- name: python-ply
	if you want to specify upgrade version for some package:
	repositories:
	- name: A-Tune
	  u_ver: x.y.z
	- name: python-py
	- name: python-ply
	then auto upgrade upgrade-example: python3 simple_update_robot.py -u repo upgrade-example master

##### 2. oa_upgradable.py 
	display all tags of target package: python3 oa_upgradable.py pkg_name
	ep: python3 oa_upgradable.py glibc
	
#### Consultation for advisors:
	if any problem, please contact: leo.fangyufa@huawei.com/leofang_94@163.com
	
	
## Contribution

1.  Fork the repository
2.  Create Feat_xxx branch
3.  Commit your code
4.  Create Pull Request

