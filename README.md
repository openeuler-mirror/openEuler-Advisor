# openEuler-Advisor

## 1、介绍

openEuler-Advisor 的目标是为 openEuler 制品仓的日常工作提供自动化的巡检和建议。

当前项目中值得关注的内容

1、upstream-info：这个目录中集中了当前openEuler项目制品仓中可见的软件组件的上游信息。

2、advisors：这个目录中提供了一些自动化脚本，其中包括：

2.1、oa_upgradable.py 这个 python 脚本基于upstream-info，用于查询软件包上游社区版本信息及版本推荐。

2.2、simple_update_robot.py 这个 python 脚本用于src-openeuler中软件包自动升级，包括：下载推荐版本源码包、修改spec、本地obs编译、创建PR及issue等。

2.3、check_missing_specs.py 这个 python 脚本，对 src-openeuler 中各2个仓库进行巡检。如果发现仓库中还不存在 spec 文件，可以直接创建相应仓库中的任务。

2.4、check_source_url.py 这个 python 脚本，对src-openeuler中各个软件包的source地址进行检查，如果地址无效或不正确，自动创建issue提示修改。

2.5、create_repo.py 和 create_repo_with_srpm 这两个 python 脚本提供了批量创建新 repo 的功能。

2.6、which_archived.py 用于检查制品仓软件的上游社区是否已经处于归档状态，便于维护团队及时调整包维护策略。

2.7、check_repeated_repo.py 用于检查src-openeuler中可能重复的软件包。

2.8、psrtool.py 用于查询软件包归属SIG及某个SIG管理的软件包列表信息

2.9、tc_reminder.py 用于自动为openeuler中TC成员创建提示信息

2.10、review_tool.py 用于生成指定软件仓PR的代码审视清单，以规范化PR审视过程。

3、prow：存放对接CI/CD框架PROW的脚本
## 2、后续计划

1、@solarhu 团队正在开发工具，计划提供 openEuler 内所有组件依赖关系的查询。

2、对 simple_update_robot.py 做进一步的优化，提高自动化处理升级的能力。

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

### 3.2、advisors介绍
#### 3.2.1 环境配置
##### a. 必要软件包安装
	pip3 install python-rpm-spec (ver>=0.10)
	pip3 install PyYAML (ver>=5.3.1)
	pip3 install requests (ver>=2.24.0)
	yum install rpmdevtools (ver>=8.3)
	pip3 install beautifulsoup4 (ver>=4.9.3)
	yum install yum-utils (ver>=1.1.31)
	
##### b. json文件配置
	创建json文件：~/.gitee_personal_token.json
	json文件格式：{"user":"gitee用户名","access_token":"token密码"}
	
	gitee token密码设置入口：https://gitee.com/profile/personal_access_tokens

##### c. gitee ssh配置
	如果未配置, 请参考：https://gitee.com/help/articles/4181

##### d. OBS配置
	如果未配置, 请参考：https://openeuler.org/zh/docs/20.09/docs/ApplicationDev/%E6%9E%84%E5%BB%BARPM%E5%8C%85.html

##### e. Python环境配置
	如果处于开发态，直接使用该工具，首先需要配置Python环境路径：source ./develop_env.sh
	
	
#### 3.2.2 使用说明
##### a. simple_update_robot.py
	单软件包自动升级: python3 simple_update_robot.py -u pkg pkg_name branch_name [-n new_version]
	例如: python3 simple_update_robot.py -u pkg snappy master
	
	单软件包手动升级: python3 simple_update_robot.py pkg_name branch_name [-fc] [-d] [-s] [-n new_version] [-b] [-p]
	例如: python3 simple_update_robot.py snappy openEuler-20.03-LTS -fc -d -s -n 1.8.1
	
	多软件包仓库升级: python3 simple_update_robot.py -u repo repo_name branch_name
	例如: python3 simple_update_robot.py -u repo src-openeuler master
	
	用户可以在本地工作目录配置自动升级yaml文件, 比如: upgrade-example.yaml
	repositories:
	- name: A-Tune
	- name: python-py
	- name: python-ply
	如果你想为某些软件包指定升级版本，可以配置为:
	repositories:
	- name: A-Tune
	  u_ver: x.y.z
	- name: python-py
	- name: python-ply
	然后通过工具自动升级upgrade-example: python3 simple_update_robot.py -u repo upgrade-example master

##### b. oa_upgradable.py 
	查询软件包上游社区信息及版本推荐: python3 oa_upgradable.py pkg_name
	例如: python3 oa_upgradable.py glibc

#### 3.2.3 advisors咨询:
	如果有其他问题或疑问, 可以邮件联系: leo.fangyufa@huawei.com/leofang_94@163.com
