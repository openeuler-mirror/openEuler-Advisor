# 发布

本项目当前包括几个子项目：数据标准定义，[数据文件](./upstream-info)，[pkgship](./packageship)，[patch-tracking](./patch-tracking), [advisor小工具](./advisor)。其中数据、各工具之间相对解耦，因此不对这个项目整体发布，而是对各子项目单独发布。


### 子项目版本命名

所有单独发布的子项目版本采用[Semver 2.0](https://semver.org/) 的 **major.minor.patch** 方式 ，参考如下场景递增对应字段：

- 当影响backword-compatibility的时候，major++。例如，和旧的API不兼容。

- 当有新的特性增加时，minor++。

- 当无新增特性，修复文档、缺陷、漏洞时， patch++。
  

### 子项目Tag命名

各子项目通过前缀区别，例如：

* 数据标准的前缀: **^api-v**。例如 `api-v1.0.0`
* patch-tracking的前缀：**^patch-tracking-v**。例如  `patch-trakcing-v1.1.0`
* pkgship的前缀: **^pkgship-v**。   例如  `pkgship-v1.2.0`
* 其他

### 分支管理

当前openEuler-Advisor处于快速发展期，因此本项目不提供**LTS**维护，当前的分支模式是**单主干 master**。

```
Q: 如果使用者（例如openEuler发行版）的LTS需要维护怎么办?
A: openEuler src-repo下面patch式维护。如果发现的问题在master上存在，欢迎提交PR

Q：是否计划提供LTS版本
A：暂无计划
```

### 发布流程及方式

- 各子项目的相关人员如果认为有必要发布版本，请提交**PR**。**PR**需要在各子项目的`ChangeLog.md`里面增加发布内容，格式如下(示例)：

```  
 发布pkgship v1.2.0:
      - 增加XXX功能
      - 修复XXX问题
```

- Maintainer同意并且合入后立即基于合入的commitid发布[release](https://gitee.com/openeuler/openEuler-Advisor/releases/new)，内容和ChangeLog.md里面**严格一致**，以上述为例：

  - **Tag Version**:  `pkgship-v1.2.0`

    注：后面建议rpm spec的`name`是 `pkgship`，`version`是`1.2.0`

  - **Release Title**: `发布pkgship v1.2.0`

  - **Release Description**: 
```
    - 增加XXX功能
    - 修复XXX问题
```

    注：后面建议rpm spec的`changelog`填入对应内容。

  - **附件**

    - 建议各子项目（尤其工具类）增加 Makefile，提供 make dist功能，生成   pkgship-v.1.2.0.tar.gz及 pkgship-v1.2.0.sha256
    - 如无，Maintainer生成对于的发布件

    注：附件的链接放入各rpm spec的SOURCE部分

### 发布件的质量要求（待补充）