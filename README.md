# openEuler-Advisor

#### 介绍
openEuler-Advisor 的目标是为 openEuler 制品仓的日常工作提供自动化的巡检和建议。

目前有两个可以工作的脚本。

1. check_upgradable.rb 这是个 ruby 脚本，可以对比制品仓中的软件相比社区上游最新版本的差异。如果发现有差异的话，可以直接推送相应仓库中的任务。
2. check_missing_specs.rb 这是个 ruby 脚本，对 src-openeuler 中各个仓库进行巡检。如果发现仓库中还不存在 spec 文件，可以直接推送相应仓库中的任务。

#### 后续计划

1. 对于 upgradable ，我们希望后续进一步增强自动化能力，对于简单的软件包实现自动化的升级，生成 PR 推送给相应仓库。

#### TODO
