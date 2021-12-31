#!/usr/bin/python3
#coding:utf-8
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2020-2020. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
#
# ******************************************************************************/
"""
This is a script to capture software package upgrade changes in the software upgrade ISSUE.
"""
import os
import sys
import argparse
import csv

from advisors import gitee


# 抓取结果分析数据
DST_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "result.csv")


def mrkd2json(inp):
    """
    Convert the Markdown list to JSON format.
    """
    variance_classification = [u"特性变化", u"配置文件", u"ABI差异", u"命令行/功能", u"SPEC文件"]
    variance_default_msg = [[u"", u"无", u"不涉及", u"NA", u"新增特性/删除特性/变更特性实现"],
                            [u"", u"无", u"不涉及", u"NA", u"新增/变更/删除配置项"],
                            [u"", u"无", u"不涉及", u"NA", u"新增/变更/删除API",
                             u"新增/变更/删除结构体"],
                            [u"", u"无", u"不涉及", u"NA", u"新增/变更/删除命令",
                             u"新增/变更/删除命令选项", u"新增/变更/删除日志输出"],
                            [u"", u"无", u"不涉及", u"NA",
                             u"新增/变更/删除 编译依赖、安装依赖、依赖的软件版本变更",
                             u"拆分软件包方式变更"]]
    variance_details = [u"", u"", u"", u"", u""]
    line_list = inp.split('\n')[1:]
    classification_index = -1
    for line_info in line_list:
        table_info = line_info.split('|')
        one_line = table_info[1:]
        if len(one_line) < 4:
            continue
        if one_line[0].strip():
            for index, variance in enumerate(variance_classification):
                if one_line[0].find(variance) != -1:
                    classification_index = index
                    temp_clasify = one_line[1]
                    temp_detail = one_line[2]
                    temp_solution = one_line[3]
                    if ((temp_clasify.strip() in variance_default_msg[classification_index] \
                        or temp_clasify.strip().strip("*") in variance_default_msg[classification_index]) \
                        and (temp_detail.strip() in variance_default_msg[classification_index] \
                            or temp_detail.strip().startswith(u"无"))\
                        and (temp_solution.strip() in variance_default_msg[classification_index] \
                            or temp_solution.strip().startswith(u"无"))):
                        continue
                    variance_details[classification_index] += u"差异项: " + temp_clasify + "\n"
                    variance_details[classification_index] += u"差异说明: " + temp_detail + "\n"
                    variance_details[classification_index] += u"影响评估与适配方案: " + temp_solution + "\n\n"
        elif classification_index != -1:
            temp_clasify = one_line[1]
            temp_detail = one_line[2]
            temp_solution = one_line[3]
            if ((temp_clasify.strip() in variance_default_msg[classification_index] \
                 or temp_clasify.strip().strip("*") in variance_default_msg[classification_index]) \
                and (temp_detail.strip() in variance_default_msg[classification_index] \
                     or temp_detail.strip().startswith(u"无"))\
                and (temp_solution.strip() in variance_default_msg[classification_index] \
                    or temp_solution.strip().startswith(u"无"))):
                continue
            variance_details[classification_index] += u"差异项: " + temp_clasify + "\n"
            variance_details[classification_index] += u"差异说明: " + temp_detail + "\n"
            variance_details[classification_index] += u"影响评估与适配方案: " + temp_solution + "\n\n"

    return variance_details

def process_one_repo(repo):
    """
    Main process of the functionality
    """
    try:
        user_gitee = gitee.Gitee()
    except NameError:
        sys.exit(1)
    issues_list = user_gitee.get_issues(repo, state="all")
    if not issues_list:
        print("WARNING: Can't find any issues of {pkg}".format(pkg=repo))
        return []

    template = None
    for issue in issues_list:
        if issue["issue_type"] == u"开源软件变更管理":
            template = issue["body"]
            break
    if not template:
        return []
    variance_details = mrkd2json(template)
    return variance_details

def main():
    """
    Main entrance of the functionality
    """
    parameters = argparse.ArgumentParser()
    parameters.add_argument("-f", "--path", type=str, help="file path of repo list")

    args = parameters.parse_args()
    soft_changes = {}
    with open(args.path, "r", encoding="utf-8") as f_repo:
        repo_list = list(x for x in list([x.strip().split() for x in f_repo.read().splitlines()]) if len(x) > 0)
        repo_size = len(repo_list)
        index = 0
        for repo in repo_list:
            index += 1
            print("processing %s/%s" % (index, repo_size))
            soft_name = repo[0]
            try:
                soft_change_info = process_one_repo(soft_name)
                if soft_change_info:
                    soft_changes[soft_name] = process_one_repo(soft_name)
                else:
                    print("processing %s, can not get the upgrade issue." % soft_name)
            except Exception as e_msg:
                print("processing %s failed. error: %s" % (soft_name, e_msg))

    rows = []
    rows.append(["name", u"特性变化", u"配置文件", u"ABI差异", u"命令行/功能", u"SPEC文件"])
    for soft_name in soft_changes:
        one_row = [soft_name]
        one_row.extend(soft_changes[soft_name])
        rows.append(one_row)
    with open(DST_FILE, "w+", encoding="utf-8-sig", newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerows(rows)

if __name__ == "__main__":
    main()

