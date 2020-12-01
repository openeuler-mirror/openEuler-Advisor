---
typora-copy-images-to: images
---

# 使用 review_tool 来改进 PR 的评审过程



v0.1 by Shinwell_Hu 

v0.2 by smileknife, update editing mode for review items

## 下载配置 review_tool

review_tool 当前是 openEuler-Advisor 的一部分，所以使用的第一步是下载完整的 openEuler-Advisor，并做基本设置

```shell
$ git clone git@gitee.com:openeuler/openEuler-Advisor
$ source openEuler-Advisor/develop_env.sh
```

review_tool 会以特定用户的身份发布 review 清单，因此需要设置个人的 gitee 账号：

在gitee个人主页的设置中，有一个 [私人令牌](https://gitee.com/profile/personal_access_tokens) 页面

![create_new_token](<./create_new_token.png>)

![create_private_token](<./create_private_token.png>)

Gitee会提示使用密码再验证一次，就可以生成 token 了。

使用这些相关信息，在个人用户目录下的 .gitee_personal_token.json 中添加以下内容：

```json
{"user":"This_is_my_gitee_ID", "access_token":"This_is_a_random_string_from_last_step"}
```



设置完成以后，就可以运行 openEuler-Advisor/advisors/review_tool.py 了。



## 使用 review_tool 的日常

比如：

```shell
$ review_tool.py -n src-openeuler/lapack -p 16 -w review_dir
```

这样就是一个典型的 执行过程。在这个命令中，review_tool会将  gitee.com/src-openeuler/lapack 仓完整的clone到"-w"指定的目录中，然后fetch 指定的 PR 16，在本地代码仓中生成 pr_16分支。然后经过相关规则，生成一份 review 清单，以用户的名义 post comment 到 PR 下。

![review_ongoing](<./review_ongoing.png>)

当前使用颜色球来表示审视状态，第一次创建的审视清单，所有审视结果都会是 &#x1F535; 的。

注意这个审视结果是一个Markdown格式的可编辑纯文本评论，可以随时使用 gitee 的评论编辑功能修改审视结果。

如果本地已经有一个完成的代码仓，这时候使用 -r 命令即可

```shell
$ review_tool.py -n src-openeuler/lapack -p 16 -w review_dir -r
```

这是review_tool会在 review_dir/lapack 代码仓中切换到 master 分支，然后执行一次 git pull。相对 clone更节省时间和带宽。

如果已经有的是一个 gitee PR 的URL，也可以用 URL代替 -n 和 -p 参数

```shell
$ review_tool.py -u https://gitee.com/src-openeuler/lapack/pulls/16 -w review_dir -r
```

这主要是为了方便拷贝粘贴。

注意：因为 review 清单是基于当前提交的具体代码生成的，所以推送新代码时，可能原有的清单需要刷新。我们建议在开发者推送新代码时，重新生成清单。

Maintainer 一方面可以通过 修改 review 清单，来表达当前review的意见和结果，也可以通过命令行来修改。比如：

```shell
$ review_tool.py -u https://gitee.com/src-openeuler/lapack/pulls/16 -e "go:0,1,2,3,4 nogo:6,7 na:5 question:8"
```

![review_resut](<./review_result.png>)

-e选项支持一个状态编辑列表，表示需要刷新的状态与对应的审视项。该列表为字符串，具体格式：

"**状态1:审视项列表1 状态2:审视项列表2 状态3:审视项列表3 ...**"

每组**状态:审视项列表**间以空格分隔；

支持5种状态：

- go  对应绿灯，审视者认为符合要求
- nogo  对应红灯，审视者认为不符合要求
- na(not applicable) 对应白灯，审视者认为与本PR无关
- question  对应黄灯，审视者无法确认是否符合要求
- ongoing  对应蓝灯，审视过程中

审视项列表中的审视项编号之间使用英文逗号分隔；

如果希望更新所有审视项到同一个状态，可以指定编辑列表为"**状态:999**"，如所有审视项全部通过，指定该参数为"go:999"即可；

该选项主要是为了帮助 maintainer 简化手动修改大清单时的麻烦。



## 如何参与改进 review_tool

review_tool 最初的想法受到 [FedoraReview](https://pagure.io/FedoraReview) 的影响。Fedora社区在引入一个新的软件包的时候，有一个相对的完整的 Review Check List。 

##FIXME: 加一个截图 ##

在其他领域中，类似最典型的是航空领域中起飞前检查清单。

##FIXME: 加一个截图##

但从 openEuler 角度看，构建/执行rpmlint等等操作，应该是CI的一部分。所以我们试图按照 openEuler 的理念实现一个能在 openEuler 社区推广的工具，而没有去尝试复用FedoraReview，因此review_tool 和 FedoraReview 在代码上没有任何的关系。



当前 review_tool 是一个使用 python 3开发的脚本，所有内容都在 openEuler-Advisor/advisors 目录内。

当前所有的审视项，都放在 helper/reviewer_checklist.yaml 里，每一项有这样四个参数：

- name，标识审视项
- condition，在什么情况下触发该审视项要求
- claim，具体的审视要求
- explain，对审视要求的说明与解释

而上述的condition，在review_tool.py中会根据PR内容来具体判断生成。

所以如果您认为需要新增的审视项，首先考虑对应的condition是否已经存在，如果不存在，就需要改进 review_tool来做额外的判断；而如果已经存在，那只需要在 reviewer_checklist.yaml 中添加相应的审视项就可以了。



注意：review_tool的目标不是取代CI过程。我们认为所有例行的可以自动化的检查工作，包括校验，构建测试等动作，都应该由CI完成。当前openEuler 社区的CI开源在 [openeuler-jenkins](https://gitee.com/openeuler/openeuler-jenkins) 中。只有必须通过 Maintainer 和开发者交互才能完成的的工作，才可以放在 review_tool 中。



另一个角度，review_tool 可以帮助开发者和 Maintainer 更快的融入 openEuler 社区，所以我们也希望所有审视项的claim和explain尽可能的简明易懂。这是社区文化传承的一种方法。
