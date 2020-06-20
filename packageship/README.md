# pkgmnt

#### 介绍
pkgmnt希望提供软件包依赖，生命周期，补丁查询等功能。
1.软件包依赖：方便社区人员在新引入、软件包更新和删除的时候能方便的了解软件的影响范围。
2.生命周期管理：跟踪upstream软件包发布状态，方便维护人员了解当前软件状态，及时升级到合理的版本。
3.补丁查询：方便社区人员了解openEuler软件包的补丁情况，方便的提取补丁内容（待规划）


#### 软件架构
系统采用flask-restful开发，使用SQLAlchemy ORM查询框架，同时支持mysql和sqlite数据库，通过配置文件的
形式进行更改


#### 安装教程

1.  安装系统的依赖包

    pip install -r requirements.txt

2.  执行打包命令，打包命令行工具,其中（pkgship）为命令行的名称，可以随意更改

    2.1 打包生成 .spec打包文件

        pyinstaller -F -n pkgship cli.py

    2.2 修改 .spec打包文件，将hiddenimports中加入如下配置
        
        hiddenimports=['pkg_resources.py2_warn']
    
    2.3 生成二进制命令文件

        pyinstaller pkgship.spec

    2.4 二进制命令文件拷贝至可运行目录

        cp dist/pkgship /usr/local/bin

3.  系统的部署

    3.1 安装uwsgi服务器

        pip install uwsgi
    
    3.2 修改服务的配置文件

        cd /etc/pkgship/

        vi package.ini
    
    备注： 配置文件中可以支撑sqlite数据库和mysql数据库，可根据相应配置进行修改

        如果需要调整 查询和修改相关端口，请同步更改  mange.ini 和selfpkg.ini 中的配置

        切记（manage.py为拥有写入权限，selfpkg为拥有查询权限）

    3.3 启动系统服务

        uwsgi -d --ini manage.ini

        uwsgi -d --ini selfpkg.ini


#### 使用说明

1.  命令行使用

    pkgship --help

2. restful接口使用

    参考接口设计文档中的接口定义，进行相关接口调用

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request


#### 会议记录
1.  2020.5.18：https://etherpad.openeuler.org/p/aHIX4005bTY1OHtOd_Zc

