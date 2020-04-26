# openEuler-Advisor

#### 介绍
advisor当前只有一些脚本，可以根据主线代码仓的tag判断当前软件是否需要升级，以及推荐升级版本。


#### 使用说明

1.  check_upstream.rb是ruby脚本，依赖svn, curl, git和hg。
2.  当前openEuler软件的版本信息来自spec文件的Version，如果没有spec文件的话，可以手动输入
3.  每个软件一个yaml。yaml文件名和spec文件名一致。当前yaml的格式：
  - version_control: 可选为svn, git, hg, github, gnome, metacpan, pypi
  - src_repo: 
  > . 如果version_control为svn，那src_repo需要 完整的 SVN 仓库地址。例子可以参考upstream-info/amanda.yaml
  > . 如果version_control为git，那src_repo需要 完整的 GIT 仓库地址。例子可以参考upstream-info/mdadm.yaml
  > . 如果version_control为hg，那src_repo需要 完整的 HG 仓库地址。例子可以参考upstream-info/nginx.yaml
  > . 如果version_control为github，那src_repo只需要 $proj/$repo 即可，不需要完整的URL。例子可以参考upstream-info/asciidoc.yaml
  > . 如果version_control为gnome，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考upstream-info/gnome-terminal.yaml。注意gitlab.gnome.org上很多项目需要访问权限，这些不能作为上游代码仓库。
  > . 如果version_control为metacpan，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考upstream-info/perl-Authen-SASL.yaml。注意在metacpan上的命名规范。
  > . 如果version_control为pypi，那src_repo只需要 $proj 即可，不需要完整的URL。例子可以参考upstream-info/python-apipkg。注意pypi上的命名规范。
  > . 如果有其它诉求，请和我联系。
  - tag_prefix: 不同项目的tag规则不同，这里比如tag是v1.1的，那么tag_prefix设置为^v即可。有些软件的tag_prefix会比较复杂。
  - seperator: 不同项目的tag中域分割不同，有些是-，有些是_，一般默认是.

#### TODO
