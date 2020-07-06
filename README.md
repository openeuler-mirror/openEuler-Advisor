# openEuler-Advisor

#### 介绍
openEuler-Advisor 的目标是为 openEuler 制品仓的日常工作提供自动化的巡检和建议。

当前项目中值得关注的内容

1. upstream-info：这个目录中集中了当前openEuler项目制品仓中可见的软件组件的上游信息。
2. advisors：这个目录中提供了一些自动化脚本，其中包括：
  2.1 oa_upgradable.py 这个 python 脚本基于upstream-info，对比制品仓中软件相比社区上游最新版本的差异。
  2.2 simple-update-robot.py 这个 python 脚本基于原有 spec 文件信息，下载社区上游指定版本，并生成新的 spec 文件和相应的 PR。
  2.3 check_missing_specs.py 这个 python 脚本，对 src-openeuler 中各个仓库进行巡检。如果发现仓库中还不存在 spec 文件，可以直接创建相应仓库中的任务。
  2.4 check_licenses.py 这个试验性的 python 脚本对指定软件组件中 spec 文件内指定的 license 和 软件tar包内的 license 做交叉验证。
  2.5 create_repo.py 和 create_repo_with_srpm 这两个 python 脚本提供了批量创建新 repo 的功能

#### 后续计划

1. @solarhu 团队正在开发工具，计划提供 openEuler 内所有组件依赖关系的查询。
2. 对 simple-update-robot.py 做进一步的优化，提高自动化处理升级的能力。
3. 完善 upstream-info，覆盖 openEuler 制品仓中所有软件。并将分散中 openEuler 社区中的各个 YAML 统一到 upstream-info 中，便于后续统一管理。
4. 完善 oa_upgradable.py 支持的上游社区代码管理协议，当前发现还需要增加 fossil 的支持。
