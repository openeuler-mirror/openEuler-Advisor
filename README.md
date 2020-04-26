# openEuler-Advisor

#### 介绍
advisor当前只有一些脚本，可以根据主线代码仓的tag判断当前软件是否需要升级，以及推荐升级版本。


#### 使用说明

1.  check_upstream.rb是ruby脚本，依赖svn, curl, git, metacpan和hg。
2.  当前openEuler软件的版本信息来自spec文件的Version，如果没有spec文件的话，可以手动输入
3.  每个软件一个yaml。当前yaml的格式：
  - version_control: 可选为svn, git, hg, github
  - src_repo: 
    > 如果version_control为github，那src_repo只需要 $proj/$repo 即可
    > 如果version_control为metacpan，那src_repo只需要 $repo 即可
    > 否则需要完整的 URL
  - tag_prefix: 不同项目的tag规则不同，这里比如tag是v1.1的，那么tag_prefix设置为^v即可。有些软件的tag_prefix会比较复杂。
  - seperator: 不同项目的tag中域分割不同，有些是-，有些是_，一般默认是.

#### TODO
1. 每次查询的结果数据保存在last_query里面
