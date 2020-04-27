# 包元数据管理
## 目的
- 确保包的来源可追溯
- 方便包的自动化更新

## 流程
- 包的提交者在提交的同时必须提供对应的[元数据信息](#元数据信息)
- CI会自动进行“相应的有效性校验”
- Maintainer进行人工审核（例如是否官方）

## 原则
- 官方

软件源码来源必须来自官方，官方包括：
1. 官方原始发布地址
2. 官方认可的镜像地址
    例如有些以github作为只读镜像，也可以作为官方地址

官方在初次提交时需要人工审核。

- 可靠

软件的获取地址必须支持 https

- 可重复

maintainer或其他人可以根据填写的元数据获取对应的代码

- 可校验

记录软件发布方提供的校验机制，包括但不限于：
1. sha
2. 签名
3. git commitid

## 元数据信息
* **`git_repo`** (string, 如果是git下载，那么此字段为 REQUIRED)

TODO 如果svn地址，那么另外增加  `svn_repo`字段。

* **`versions`** (array of [`version`](#版本字段))

软件的具体的版本列表，列表中的版本正式进入openEuler仓库。


### 例子
```
git_repo: https://github.com/template/template.git

```


## 模板
模板可[参见](./template.yaml)
