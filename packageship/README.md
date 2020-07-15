<img src="doc/design/pkgimg/pkgship-logo.png" width="50%" height="50%"/>

[English](./README.md) | 简体中文

# pkgship

## 介绍
pkgship是一款管理OS软件包依赖关系，提供依赖和被依赖关系的完整图谱查询工具，pkgship提供软件包依赖，生命周期，补丁查询等功能。
1.  软件包依赖：方便社区人员在新引入、软件包更新和删除的时候能方便的了解软件的影响范围。
2.  生命周期管理：跟踪upstream软件包发布状态，方便维护人员了解当前软件状态，及时升级到合理的版本。
3.  补丁查询：方便社区人员了解openEuler软件包的补丁情况，方便的提取补丁内容


### 软件架构
系统采用flask-restful开发，使用SQLAlchemy ORM查询框架，同时支持mysql和sqlite数据库，通过配置文件的形式进行更改


一、安装pkgship
---
支持操作系统：openEuler 1.0及以上版本
#### 1.环境准备 

#### 1.1 Dnf工具

#### 1.2 Python环境

##### 安装 DNF 
1. 为了安装 DNF ，您必须先安装并启用 epel-release 依赖。
在系统中执行以下命令：
```
yum install epel-release
或
yum install epel-release -y
```
2. 使用 epel-release 依赖中的 YUM 命令来安装 DNF 包
在系统中执行以下命令：
```
yum install dnf
```
##### 安装 python环境
```
dnf install python3-devel
dnf install python3
```
安装python依赖包(批量安装)
```
dnf install python3-pip
```


#### 2.安装pkgship

```
dnf install pkgship（版本号）
```
---

### 安装在容器中（适用于开发者）

#### 1. docker使用

#### 1.1 下载源的更改
更改repo的源配置

```
    >[everything]
    name=everything
    baseurl=https://repo.openeuler.org/openEuler-20.03-LTS/everything/aarch64/
    enabled=1
    gpgcheck=0
    priority=1

    >[source]
    name=source
    baseurl=https://repo.openeuler.org/openEuler-20.03-LTS/source/
    enabled=1
    gpgcheck=0
    priority=2
```

#### 1.2 docker镜像的加载使用

搜索openeuler相关的docker镜像
```
docker search openeuler
```


获取docker镜像，以kunpengcompute/openeuler镜像为主（官方维护）
```
docker pull kunpengcompute/openeuler
```

以命令的模式进行docker
```
docker run -itd kunpengcompute/openeuler /bin/bash
```

启动已经停止的docker容器
```
docker start 容器id
docker attach 容器id
```

#### 2. 系统的安装部署

#### 2.1 软件的安装

```
rpm -ivh rpm包
```
或者
```
dnf install pkgship-(版本号)
```

#### 2.2 系统的配置

创建初始化数据库的yaml配置文件
```
- dbname: openEuler-20.03-LTS
  src_db_file:
- /etc/pkgship/src.sqlite
  bin_db_file:
- /etc/pkgship/bin.sqlite
  status: enable
  priority: 1
```

更改系统的默认配置文件(根据实际情况进行配置更改)

```
vim /etc/pkgship/package.ini
```

#### 2.3 服务启动

```
pkgshipd start
```

##### 2.4 服务的停止
```
pkgshipd stop
```

#### 2.5. 数据库初始化
```
pkgship init
```
	
二、使用说明
---
### 1. 单包查询

1. 查询源码包(sourceName)在所有数据库中的信息 
```
pkgship  sourceName
```
2. 查询当前包(sourceName)在指定数据库(dbName)中的信息
```
pkgship  sourceName  -db  dbName
```
### 2. 查询所有包
1. 查询所有数据库下包含的所有包的信息
```
pkgship  list
```
2. 查询指定数据(dbName)下的所有包的信息
```
pkgship  list  -db  dbName
```    
### 3. 安装依赖查询
1. 查询二进制包(binaryName)的安装依赖,按照优先级轮询默认数据库
``` 
pkgship  installdep  binaryName
``` 
2. 在指定数据库(dbName)下查询二进制包(binaryName)的所有安装依赖
按照先后顺序指定数据库查询的优先级
``` 
pkgship  installdep  binaryName -dbs  dbName1  dbName2...
``` 
### 4. 编译依赖查询
1. 查询源码包(sourceName)的所有编译依赖,按照优先级轮询默认数据库
``` 
pkgship  builddep  sourceName
``` 
2. 在指定数据库(dbName)下查询源码包(sourceName)的所有安装依赖
按照先后顺序指定数据库查询的优先级
``` 
pkgship  builddep  sourceName  -dbs  dbName1  dbName2...
``` 
### 5. 自编译自安装依赖查询
1. 查询二进制包(binaryName)的安装依赖,按照优先级轮询默认数据库
``` 
pkgship  selfbuild  binaryName
``` 
2. 查询源码包(sourceName )的编译依赖
``` 
pkgship  selfbuild  sourceName  -t  source 
``` 
3. 其他参数
-dbs 指定数据库优先级.
``` 
示例: pkgship  selfbuild  binaryName  -dbs dbName1 dbName2 
``` 
-s 是否查询自编译依赖
默认为0不查询自编译依赖,可以指定0或1(表示查询自编译)
``` 
查询自编译示例:pkgship  selfbuild  sourceName  -t  source  -s  1
``` 
-w 是否查询对应包的子包.默认为0,不查询对应子包,可以指定 0或1(表示查询对应子包)
``` 
查询子包示例: pkgship  selfbuild  binaryName  -w 1
``` 
### 6. 被依赖查询
1. 查询源码包(sourceName)在某数据库(dbName)中被哪些包所依赖
查询结果默认不包含对应二进制包的子包 
``` 
pkgship  bedepend  sourceName  -db  dbName
``` 
2. 使查询结果包含二进制包的子包 加入参数 -w
``` 
pkgship  bedepend  sourceName  -db dbName  -w  1 
``` 
### 7. 修改包信息记录
1. 变更数据库中(dbName)源码包(sourceName)的maintainer 为Newmaintainer 
```
pkgship  updatepkg  sourceName  db  dbName  -m  Newmaintainer 
```
2. 变更数据库中(dbName)源码包(sourceName)的maintainlevel为Newmaintainlevel 
```
pkgship  updatepkg  sourceName  db  dbName  -l  Newmaintainlevel 
```
3. 同时变更数据库中(dbName)源码包(sourceName)的maintainer 为Newmaintainer和变更maintainlevel为Newmaintainlevel
```  
pkgship updatepkg sourceName db dbName -m Newmaintainer -l  Newmaintainlevel
```
### 8. 删除数据库
删除指定数据库(dbName)
```
pkgship rm db dbName
```

三、参与贡献
---
我们非常欢迎新贡献者加入到项目中来，也非常高兴能为新加入贡献者提供指导和帮助。在您贡献代码前，需要先签署[CLA](https://openeuler.org/en/cla.html)。

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request


### 会议记录
1.  2020.5.18：https://etherpad.openeuler.org/p/aHIX4005bTY1OHtOd_Zc

