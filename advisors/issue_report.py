#!/usr/bin/env python3

"""
Description:generate issue report
"""
# pylint: disable=inconsistent-return-statements
# pylint: disable=broad-except
# pylint: disable=no-else-return
# pylint: disable=too-many-locals
import copy
import os
import sys
import json
import pandas as pd
import requests

FILE_NAME = sys.argv[0]
CMD_INPUT_ARGS = sys.argv[1:]


def _to_markdown(df: pd.DataFrame, index=False):
    cols = df.columns
    title = "|" + "|".join(str(col) for col in cols) + "|\n"
    under_title = "|" + "---|" * len(cols) + "\n"

    content = ""
    for idx, row in df.iterrows():
        curr_row = list(str(r) for r in row)
        if index:
            curr_row.insert(idx)
        content += "|" + "|".join(curr_row) + "|\n"

    return title + under_title + content

def parse_args(name, input_args):
    """
    解析输入的参数
    Args:
        name: 运行文件名
        input_args: 解析出来的参数

    Returns:
        issue_params, cve_params, output_path
    """
    split_index = 0
    if "-milestone" not in input_args or "-branch" not in input_args:
        print(
            "usage: {} [-milestone [Required parameters]] [-branch [Required parameters]] "
            "[-outpath [Optional parameters]]".format(name)
        )
        return
    if "-outpath" not in input_args and (
        "/" in input_args[-1] or "\\" in input_args[-1]
    ):
        print(
            "Missing -outpath \n"
            "usage: {} [-milestone [Required parameters]] [-branch [Required parameters]] "
            "[-outpath [Optional parameters]]".format(name)
        )
        return
    for index, con in enumerate(input_args):
        if con == "-branch":
            split_index = index
    issue_params = input_args[1:split_index]
    cve_params = (
        input_args[split_index + 1 : len(input_args) - 2]
        if "-outpath" in input_args
        else input_args[split_index + 1 :]
    )
    output_path = input_args[-1] if "-outpath" in input_args else "./"
    if not os.path.exists(output_path):
        print("The output path is illegal, please re-enter!")
        return
    return issue_params, cve_params, output_path


def build_request_parameters(issue_params, cve_params):
    """
    构建请求参数
    Args:
        issue_params: Issue请求参数
        cve_params: cve请求参数

    Returns:
        issue_params_list, cve_params_list
    """
    parameters_issue = {
        "community": "openeuler",
        "state": "all",
        "milestone": "",
        "sortKey": "closed_at",
        "sortValue": "descending",
    }
    parameters_cve = {
        "community": "openeuler",
        "state": "all",
        "milestone": "",
        "sortKey": "closed_at",
        "sortValue": "descending",
    }
    issue_params_list, cve_params_list = [], []
    for issue_con in issue_params:
        parameters_issue["milestone"] = issue_con
        issue_params_list.append(copy.copy(parameters_issue))
    for cve_con in cve_params:
        parameters_cve["milestone"] = cve_con
        cve_params_list.append(copy.copy(parameters_cve))
    return issue_params_list, cve_params_list


def query_issue_response(parameters_issue):
    """
    获取issue响应
    Args:
        parameters_issue: 请求参数

    Returns:
        response_issue_string
    """
    url_issue = "http://omapi.osinfra.cn/IssueData"
    try:
        response_issue = requests.post(
            url_issue,
            data=json.dumps(parameters_issue),
            headers={"Content-type": "application/json"},
        )
    except Exception as error:
        print(error)
        return None
    if response_issue.status_code == 200:
        response_issue_string = response_issue.json()["data"]
        return response_issue_string
    else:
        print(response_issue.status_code)
        return []


def query_cve_response(parameters_cve):
    """
    获取cve响应
    Args:
        parameters_cve: 请求参数

    Returns:
        response_cve_string
    """
    url_cve = "http://omapi.osinfra.cn/CVEData"
    try:
        response_cve = requests.post(
            url_cve,
            data=json.dumps(parameters_cve),
            headers={"Content-type": "application/json"},
        )
    except Exception as error:
        print(error)
        return None
    if response_cve.status_code == 200:
        response_cve_string = response_cve.json()["data"]
        return response_cve_string
    else:
        print(response_cve.status_code)
        return []


# pylint: disable=unused-variable
def filter_cve_content(sources):
    """
    去除cve数据中type字段不是“CVE和安全问题”的元素
    Args:
        sources: cve响应数据

    Returns:
        filter_source
    """
    filter_source = []
    for index, response in enumerate(sources):
        if response.get("type") == "CVE和安全问题":
            filter_source.append(response)
    return filter_source


def generate_csv(issue_sources, cve_sources, output_path):
    """
    将获取的issue数据按照模板输出csv文件
    Args:
        issue_sources: issue响应数据
        cve_sources: cve响应数据
        output_path: 输出路径

    Returns:
        csv文件
    """
    issue_id = []
    issue_type = []
    issue_title = []
    owner = []
    state = []
    plan_deadline_at = []
    closed_at = []
    progress = []
    version = []

    for response in issue_sources:
        issue_id.append(response.get("issue_id", "暂无相应信息"))
        issue_type.append(response.get("type", "暂无相应信息"))
        issue_title.append(response.get("issue_title", "暂无相应信息"))
        owner.append(response.get("assignee_name", "暂无相应信息"))
        state.append(response.get("state", "暂无相应信息"))
        plan_deadline_at.append(response.get("plan_deadline_at", "暂无相应信息"))
        closed_at.append(response.get("closed_at", "暂无相应信息"))
        progress.append(response.get("plan_start_at", "暂无相应信息"))
        version.append(response.get("milestone", "暂无相应信息"))
    for response in cve_sources:
        issue_id.append(response.get("issue_id", "暂无相应信息"))
        issue_type.append(response.get("type"))
        issue_title.append(response.get("issue_title", "暂无相应信息"))
        owner.append(response.get("assignee_name", "暂无相应信息"))
        state.append(response.get("state", "暂无相应信息"))
        progress.append(response.get("plan_start_at", "暂无相应信息"))
        plan_deadline_at.append(response.get("plan_deadline_at", "暂无相应信息"))
        closed_at.append(response.get("closed_at", "暂无相应信息"))
        version.append(
            ",".join(
                [
                    con.replace(":受影响", "").replace(":不受影响", "")
                    for con in response["milestone"].split(",")
                ]
            )
        )
    # 字典中的key值即为csv中列名
    dataframe = pd.DataFrame(
        {
            "Issue": issue_id,
            "类型": issue_type,
            "概述": issue_title,
            "责任人": owner,
            "状态": state,
            "计划合入时间": plan_deadline_at,
            "实际关闭时间": closed_at,
            "进展": progress,
            "所属版本": version,
        }
    )
    dataframe.to_csv(output_path + "/Issue管理报告.csv", index=False, encoding="utf_8_sig")


def generate_md(issue_sources, cve_sources, output_path):
    """
    将获取的issue数据按模板输出MD文件
    Args:
        issue_sources: issue响应数据
        cve_sources: cve响应数据
        output_path: 输出路径

    Returns:
        MD文件
    """
    description_feature_list = "## 特性清单"
    description_issue_list = "## 解决问题清单"
    description_todo_list = "## 遗留问题清单"
    description_cve_list = "## 解决CVE清单"
    feature_id = []
    feature_issue_title = []
    feature_version = []
    fixed_issue_id = []
    fixed_issue_title = []
    fixed_version = []
    todo_issue_id = []
    todo_issue_title = []
    effect = []
    todo_version = []
    for response in issue_sources:
        if response.get("type") == "需求":
            feature_id.append(response.get("issue_id", "暂无相应信息"))
            feature_issue_title.append(response.get("issue_title", "暂无相应信息"))
            feature_version.append(response.get("milestone", "暂无相应信息"))
        elif response.get("type") == "缺陷" and response.get("state") == "closed":
            fixed_issue_id.append(response.get("issue_id", "暂无相应信息"))
            fixed_issue_title.append(response.get("issue_title", "暂无相应信息"))
            fixed_version.append(response.get("milestone", "暂无相应信息"))
        elif response.get("type") == "缺陷" and response.get("state") == "open":
            todo_issue_id.append(response.get("issue_id", "暂无相应信息"))
            todo_issue_title.append(response.get("issue_title", "暂无相应信息"))
            effect.append(response.get("description", "暂无相应信息"))
            todo_version.append(response.get("milestone", "暂无相应信息"))

    dataframe_feature = pd.DataFrame(
        {"Issue": feature_id, "概述": feature_issue_title, "所属版本": feature_version}
    )
    dataframe_feature_str = _to_markdown(dataframe_feature)

    dataframe_fixed_issue = pd.DataFrame(
        {"Issue": fixed_issue_id, "概述": fixed_issue_title, "所属版本": fixed_version}
    )
    
    count = 0
    for col in dataframe_fixed_issue:
        if count < 5:
            print(col)

        count += 1
    dataframe_fixed_issue_str = _to_markdown(dataframe_fixed_issue)
 
    dataframe_todo_issue = pd.DataFrame(
        {
            "Issue": todo_issue_id,
            "概述": todo_issue_title,
            "影响分析": effect,
            "所属版本": todo_version,
        }
    )


    dataframe_todo_issue_str = _to_markdown(dataframe_todo_issue)

    cve_id = []
    openeuler_score = []
    cve_issue_title = []
    cve_version = []
    for response in cve_sources:
        cve_id.append(response.get("issue_id", "暂无相应信息"))
        openeuler_score.append(response.get("openeuler_score", "暂无相应信息"))
        cve_issue_title.append(response.get("issue_title", "暂无相应信息"))
        cve_version.append(
            ",".join(
                [
                    con.replace(":受影响", "").replace(":不受影响", "")
                    for con in response["milestone"].split(",")
                ]
            )
        )
    dataframe_cve = pd.DataFrame(
        {
            "Issue": cve_id,
            "分值": openeuler_score,
            "概述": cve_issue_title,
            "所属版本": cve_version,
        }
    )
    dataframe_cve_str = _to_markdown(dataframe_cve)

    string = (
        description_feature_list,
        dataframe_feature_str,
        description_issue_list,
        dataframe_fixed_issue_str,
        description_todo_list,
        dataframe_todo_issue_str,
        description_cve_list,
        dataframe_cve_str,
    )
    strings = "\n".join(string)

    with open(output_path + "/Issue结果报告.md", "w") as text_file:
        text_file.write(strings)


# pylint: disable=broad-except
def main():
    """
    Function main program
    Returns:

    """
    try:
        issue_params, cve_params, output_path = parse_args(FILE_NAME, CMD_INPUT_ARGS)
    except Exception as error:
        print(error)
    else:
        parameters_issues, parameters_cves = build_request_parameters(
            issue_params, cve_params
        )
        issue_con, cve_con = [], []
        for parameters_issue in parameters_issues:
            issue_con.extend(query_issue_response(parameters_issue))
        for parameters_cve in parameters_cves:
            cve_con.extend(query_cve_response(parameters_cve))
        filter_cve_con = filter_cve_content(cve_con)
        generate_csv(issue_con, filter_cve_con, output_path)
        generate_md(issue_con, filter_cve_con, output_path)


main()
