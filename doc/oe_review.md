# openEuler Pull Request Review Tool 用户使用指南

## 简介
oe_review（全称 openEuler Pull Request Review Tool）是一个用于自动化审核 openEuler 项目中的 Pull Request (PR) 的工具。它通过结合 AI 模型和人工审核，帮助开发者快速、高效地处理 PR。该工具支持多种 AI 模型，包括本地模型和云端模型，并提供了灵活的配置选项。

## 安装与配置

### 1. 安装依赖
确保您的系统已安装以下依赖：

- Python 3.x
- requests 库
- yaml 库
- chromadb 库
- openai 库

建议考虑通过如下命令安装和初始化：
```bash
python3 -m venv oE_ENV # 在当前目录下初始化虚拟环境
source oE_ENV/bin/active # 使用 oE_ENV 作为 python 运行的虚拟环境
source developer.sh # 引入 openEuler-Advisor 进入 python 运行环境
pip install requests pyyaml pyrpm  chromadb openai
```

### 2. 配置文件
创建 ~/.config/openEuler-Advisor/config.ini 配置文件，内容如下：

```config
[editor] 
# 所有 PR 审视内容提交前会由审核者本地编辑，因此需要配置一个本地的编辑器。
# 比如 console 下的 vim 或者 osx 上的 neovide。此处需要确保 编辑器 在运行过程中阻塞程序逻辑继续执行，比如对于
# neovide 来说，要配置 option 为 --no-fork 来保证这一点。
command = vim
option = "" 

[filter]
# 基于 label，提交者，代码仓或者sig 来过滤要处理的 PR
labels = lgtm-shinwell
# 比如通过 lgtm-shinwell，过滤掉 community 中 shinwell 已经发表过 /lgtm 意见的 PR
submitters = user1
repos = repo1 repo2
sigs = sig1 sig2

[community]
# 指明本地准备的 openEuler 社区管理代码仓
community = "~/Projects/openEuler/community"
release-manage = "~/Projects/openEuler/release-management"

[local]
# 支持本地运行的大模型服务
method = ollama
base_url = http://localhost:11434/api
model = "llama3.1:8b"

# 以下可按实际需要配置
[deepseek]
model = deepseek-chat
api_key = your_api_key_here
base_url = https://api.deepseek.com
method = openai

[bailian]
model = deepseek-v3
api_key = your_api_key_here
base_url = https://dashscope.aliyuncs.com/compatible-mode/v1
method = openai

[siliconflow]
model = deepseek-r1
api_key = your_api_key_here
base_url = https://api.siliconflow.cn/v1/
method = openai
```

### 3. 设置GITEE API 的 token 变量
保存在 ~/.gitee_personal_token.json
```json
{"access_token":"place_your_access_token_here", "user":"shinwell_hu"}
```

## 使用说明
### 1. 命令行参数
该工具支持以下命令行参数：

. -q, --quite: 禁用所有日志输出。
. -v, --verbose: 启用详细日志输出。
. -a, --active_user: 以维护者或提交者身份审核所有仓库中的 PR。
. -n, --repo: 指定仓库名称（包括组名）。
. -p, --pull: 指定 PR 的 ID。
. -u, --url: 指定 PR 的 URL。
. -s, --sig: 当 --active_user 启用时，审核指定 SIG 中的所有 PR。
. -m, --model: 选择用于生成审核的 AI 模型。
. -e, --editor: 选择用于编辑内容的编辑器，默认为 nvim。
. -i, --intelligent: 选择智能模型（local、deepseek、no）。
. -o, --editor-option: 编辑器的命令行选项。

### 2. 审核单个 PR
要审核单个 PR，可以使用以下命令：

```bash
python3 advisors/oe_review.py -n src-openeuler/repo_name -p 123 -i local
```
或者使用 PR 的 URL：
```bash
python3 advisors/oe_review.py -u https://gitee.com/src-openeuler/repo_name/pulls/123 -i deepseek
```
### 3. 审核整个 SIG 的 PR
如果您是某个 SIG 的维护者或提交者，可以使用以下命令审核该 SIG 中的所有 PR：
```bash
python3 advisors/oe_review.py -a -s sig_name -i no
```
### 4. 使用不同的 AI 模型
您可以通过 -i 参数选择不同的 AI 模型。例如，使用 deepseek 模型：
```bash
python3 advisors/oe_review.py -n src-openeuler/repo_name -p 123 -i deepseek
```
### 5. 手动编辑审核内容
在审核过程中，工具会调用指定的编辑器（默认为 nvim）来编辑审核内容。您可以通过 -e 参数指定其他编辑器：
```bash
python3 advisors/oe_review.py -n src-openeuler/repo_name -p 123 -e vim
```
## 审核流程
- 生成待审核 PR 列表: 工具会从指定的仓库或 SIG 中获取所有待审核的 PR。
- 简单分类: 工具会根据 PR 的标签和状态进行简单分类，决定是否可以直接关闭或合并。
- AI 审核: 对于需要进一步审核的 PR，工具会调用 AI 模型生成审核意见。
- 人工审核: 工具会调用指定的编辑器，允许用户手动编辑 AI 生成的审核意见。
- 提交审核: 工具会将最终的审核意见提交到 Gitee。

## 常见问题
### 1. 如何配置 AI 模型？
在配置文件中，您可以为不同的 AI 模型（如 deepseek、bailian、siliconflow）配置 API Key 和模型名称。确保您已正确填写这些信息。

### 2. 如何过滤不需要审核的 PR？
在配置文件的 [filter] 部分，您可以指定需要过滤的标签、提交者和仓库。工具会自动跳过这些 PR。

### 3. 如何查看详细的日志输出？
使用 -v 或 --verbose 参数可以启用详细日志输出，帮助您调试和了解工具的运行情况。

## 结论
openEuler Pull Request Review Tool 是一个强大的工具，能够帮助开发者高效地审核和管理 openEuler 项目中的 PR。通过结合 AI 模型和人工审核，它能够显著提高审核效率，减少人工工作量。希望本指南能帮助您更好地使用该工具。