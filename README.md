# openEuler-Advisor

## 1、介绍

openEuler-Advisor 的目标是为 openEuler 制品仓的日常工作提供自动化的巡检和建议。

当前项目中值得关注的内容

1、upstream-info：这个目录中集中了当前openEuler项目制品仓中可见的软件组件的上游信息。

2、advisors：这个目录中提供了一些自动化脚本，其中包括：

2.1、oa_upgradable.py 这个 python 脚本基于upstream-info，对比制品仓中软件相比社区上游最新版本的差异。

2.2、simple-update-robot.py 这个 python 脚本基于原有 spec 文件信息，下载社区上游指定版本，并生成新的 spec 文件和相应的 PR。

2.3、check_missing_specs.py 这个 python 脚本，对 src-openeuler 中各2个仓库进行巡检。如果发现仓库中还不存在 spec 文件，可以直接创建相应仓库中的任务。

2.4、check_licenses.py 这个试验性的 python 脚本对指定软件组件中 spec 文件内指定的 license 和 软件tar包内的 license 做交叉验证。

2.5、create_repo.py 和 create_repo_with_srpm 这两个 python 脚本提供了批量创建新 repo 的功能。2.6、check_abi.py 这个python脚本可以比较新老版本的rpm包，生成两个版本ABI差异分析结果。

## 2、后续计划

1、@solarhu 团队正在开发工具，计划提供 openEuler 内所有组件依赖关系的查询。

2、对 simple-update-robot.py 做进一步的优化，提高自动化处理升级的能力。

3、完善 upstream-info，覆盖 openEuler 制品仓中所有软件。并将分散中 openEuler 社区中的各个 YAML 统一到 upstream-info 中，便于后续统一管理。

4、完善 oa_upgradable.py 支持的上游社区代码管理协议，当前发现还需要增加 fossil 的支持。


## 3、小工具使用说明：

###  3.1、yaml 文件规范

src-openEuler 仓库中的yaml 文件名称与仓库名称应该保持一致，例如glibc 仓库中存放的yaml 文件名称为"glibc.yaml"，文件放在仓库根目录下
yaml 文件中需要人工填写的字段有 version_control、src_repo、tag_prefix、separator，其他内容为自动生成的，不需要填写。

#### 3.1.1、yaml字段介绍

##### **1、version_control:** 

上游仓库使用的版本控制协议，目前支持svn, git, hg, github, gnome, metacpan, pypi

##### **2、src_repo:**

上游仓库的实际地址，通过version_control 和 src_repo 我们可以使用工具下载对应的代码

##### **3、tag_prefix：**

上游仓库的tag 中version 前缀，如果是 git 协议，通过 git tag 命令即可显示所有tag。如果上游给的tag 是 v1_0_1, 那么tag_prefix 应该配置为"^v"，我们通过匹配tag_prefix即可取出正确的版本信息得到 1_0_1

##### **4、separator:** 

tag中版本的间隔符，如果 tag是 v1_0_1，然后配置separator 为"_"，我们通过代码解析可以得到正确的版本号"1.0.1"

#### 3.1.2、字段的具体要求与示例

##### 1、src_repo:

1） 如果version_control为svn，那src_repo需要 完整的 SVN 仓库地址。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/amanda.yaml

2）如果version_control为git，那src_repo需要 完整的 GIT 仓库地址。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/mdadm.yaml

3）如果version_control为hg，那src_repo需要 完整的 HG 仓库地址。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/nginx.yaml

4）如果version_control为github，那src_repo只需要 proj/repo 即可，不需要完整的URL。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/asciidoc.yaml

5） 如果version_control为gnome，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/gnome-terminal.yaml， 注意gitlab.gnome.org上很多项目需要访问权限，这些不能作为上游代码仓库。

6）如果version_control为metacpan，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/perl-Authen-SASL.yaml，注意在metacpan上的命名规范。

7） 如果version_control为pypi，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考 https://gitee.com/openeuler/openEuler-Advisor/blob/master/upstream-info/python-apipkg ，注意pypi上的命名规范。

##### 2、tag_prefix:

 不同项目的tag规则不同，这里比如tag是v1.1的，那么tag_prefix设置为^v即可。

##### 3、separator: 

不同项目的tag中域分割不同，有些是"-"，有些是"_"，一般默认是"."，建议加上双引号

#### 3.1.3、开源软件上游代码仓信息的验证方法

##### 1）常见代码配置管理方法

  git，svn，hg都可以在不下载完整代码仓的情况下获取代码仓的信息。方法如下：

\- git:

   git ls-remote --tags $repo_url

\- svn:

    svn ls -v $repo_url/tags

\- hg:

    curl $repo_url/json-tags

##### 2）常见代码托管网站的使用方法

\- github

   curl https://api.github.com/repos/$user/$repo/release

   可以获得json格式完整的release信息清单。但是不是所有项目都支持

   curl https://api.github.com/repos/$user/$repo/tags

   可以获得json格式完整的tag信息清单。但也不是所有项目都支持，并且已经发现有些项目的这个信息是错误的。

\- metacpan

   curl https://fastapi.metacpan.org/release/$repo

   可以获得json格式的最新版本信息

\- pypi

   curl https://pypi.org/pypi/$repo/json

   可以获得项目最新发布版本的信息

\- tag_prefix和tag_pattern的使用

  很多软件的tag信息设置是使用了前缀的，比如release-1.2.3，或者v1.2.3。

  设置了tag_prefix，就会把所有tag字符串中同样的前缀部分都删除。

  比如一个软件同时存在 1.2.3 和 release-1.2.2 两个tag，设置tag_prefix为release-，处理后的tag为1.2.3和1.2.2。

  tag_pattern是为了更复杂的形态使用的，不推荐使用。

\- separator 的使用

  设置separator，可以简单的把这个字符替换成"."。

  有些软件的tag分域采用的不是"."，这时候设置separator就可以规范化版本tag。

  如果软件tag分域本来就是"."，这个时候设置separator是不影响结果的。

### 3.2、Introduction of advisors
#### 3.2.1 Enviroment Setting
##### a. necessary packages install
	pip3 install python-rpm-spec (ver:0.9)
	pip3 install PyYAML (ver:5.3.1)
	
##### b. json file config
	~/.gitee_personal_token.json
	content format: {"user":"user_name","access_token":"token_passwd"}
	
	setting personal access token: https://gitee.com/profile/personal_access_tokens
	
#### 3.2.2 Use Instructions
##### a. simple-update-root.py
	single package auto-upgrade: python3 simple-update-root.py -u pkg pkg_name branch_name
	ep: python3 simple-update-root.py -u pkg snappy master
	
	single package manual upgrade: python3 simple-update-root.py pkg_name branch_name [-fc] [-d] [-s] [-n new_version] [-p]
	ep: python3 simple-update-root.py snappy openEuler-20.03-LTS -fc -d -s -n 1.8.1
	
	multi-packages in a repo auto-upgrade: python3 simple-update-root.py -u repo repo_name branch_name
	ep: python3 simple-update-root.py -u repo src-openeuler master

##### b. oa_upgradable.py 
	display all tags of target package: python3 oa_upgradable.py pkg_name
	ep: python3 oa_upgradable.py glibc

#### 3.2.3 Consultation for advisors:
	if any problem, please contact: leo.fangyufa@huawei.com/leofang_94@163.com
	
	
### 3.3、checkabi 功能介绍

checkabi 功能依赖libabigail 软件包，使用checkabi 功能前需要安装libabigail ，checkabi  提供了2个功能，下面分别介绍。

#### 3.3.1 比较rpm ABI 差异

命令行：./check_abi.py compare_rpm -r  **old.rpm new.rpm** -d **old-debuginfo.rpm new-debuginfo.rpm** 

生成的结果存放到 /var/tmp/ 下 文件名为：xx_all_abidiff.out

#### 3.3.2 比较动态库ABI差异

命令行：./check_abi.py compare_so -s ./old/usr/lib64/libssl.so.1.1.1  ./new/usr/lib64/libssl.so.1.1.1f
