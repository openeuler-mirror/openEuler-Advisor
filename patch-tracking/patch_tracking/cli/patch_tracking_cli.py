#!/usr/bin/env python3
"""
command line of creating tracking item
"""
import argparse
import os
import sys
import pandas
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def query_table(args):
    """
    query table
    """
    server = args.server

    if args.table == "tracking":
        url = '/'.join(['https:/', server, 'tracking'])
        params = {'repo': args.repo, 'branch': args.branch}
        try:
            ret = requests.get(url, params=params, verify=False)
            if ret.status_code == 200 and ret.json()['code'] == '2001':
                return 'success', ret

            return 'error', ret
        except Exception as exception:
            return 'error', 'Connect server error: ' + str(exception)
    elif args.table == "issue":
        url = '/'.join(['https:/', server, 'issue'])
        params = {'repo': args.repo, 'branch': args.branch}
        try:
            ret = requests.get(url, params=params, verify=False)
            if ret.status_code == 200 and ret.json()['code'] == '2001':
                return 'success', ret

            return 'error', ret
        except Exception as exception:
            return 'error', 'Connect server error: ' + str(exception)
    return 'error', 'table ' + args.table + ' not found'


def add_param_check_url(params, file_path=None):
    """
    check url
    """
    scm_url = f"https://github.com/{params['scm_repo']}/tree/{params['scm_branch']}"
    url = f"https://gitee.com/{params['repo']}/tree/{params['branch']}"
    patch_tracking_url = f"https://{params['server']}"
    server_ret = server_check(patch_tracking_url)
    if server_ret[0] != 'success':
        return 'error'

    scm_ret = repo_branch_check(scm_url)
    if scm_ret[0] != 'success':
        if file_path:
            print(
                f"scm_repo: {params['scm_repo']} and scm_branch: {params['scm_branch']} check failed. \n"
                f"Error in {file_path}. {scm_ret[1]}"
            )
        else:
            print(f"scm_repo: {params['scm_repo']} and scm_branch: {params['scm_branch']} check failed. {scm_ret[1]}")
        return 'error'
    ret = repo_branch_check(url)
    if ret[0] != 'success':
        if file_path:
            print(f"repo: {params['repo']} and branch: {params['branch']} check failed. {ret[1]}. Error in {file_path}")
        else:
            print(f"repo: {params['repo']} and branch: {params['branch']} check failed. {ret[1]}.")
        return 'error'
    return None


def server_check(url):
    """
    check if patch_tracking server start
    """
    try:
        ret = requests.head(url=url, verify=False)
    except Exception as exception:
        print(f"Error: Cannot connect to {url}, please make sure patch-tracking service is running.")
        return 'error', exception
    if ret.status_code == 200 or ret.status_code == 404:
        return 'success', ret

    print(f"Unexpected Error: {ret.text}")
    return 'error', ret.text


def repo_branch_check(url):
    """
    check if repo/branch exist
    """
    headers = {
        "User-Agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " +
        "Ubuntu Chromium/83.0.4103.61 Chrome/83.0.4103.61 Safari/537.36"
    }
    try:
        ret = requests.get(url=url, headers=headers)
    except Exception as exception:
        return 'error', exception
    if ret.status_code == 404:
        return 'error', f'{url} not exist.'
    if ret.status_code == 200:
        return 'success', ret

    return 'error', ret.text


def latin1_encode(text):
    """ latin1 encode """
    try:
        text.encode("latin1")
    except UnicodeEncodeError as err:
        return str(err)
    return None


def params_input_track(params, file_path=None):
    """
    load tracking from command line arguments
    """
    if not check_add_param(params):
        return 'error', 'Check input params error'

    if add_param_check_url(params, file_path) == 'error':
        return 'error', 'Check input params error.'

    repo = params['repo']
    branch = params['branch']
    scm_repo = params['scm_repo']
    scm_branch = params['scm_branch']
    version_control = params['version_control'].lower()
    enabled = params['enabled'].lower()
    server = params['server']
    user = params['user']
    password = params['password']

    err = latin1_encode(user)
    if err:
        return "error", "ERROR: user: only latin1 character set are allowed."
    err = latin1_encode(password)
    if err:
        return "error", "ERROR: user: only latin1 character set are allowed."

    enabled = bool(enabled == 'true')

    url = '/'.join(['https:/', server, 'tracking'])
    data = {
        'version_control': version_control,
        'scm_repo': scm_repo,
        'scm_branch': scm_branch,
        'repo': repo,
        'branch': branch,
        'enabled': enabled
    }
    try:
        ret = requests.post(url, json=data, verify=False, auth=HTTPBasicAuth(user, password))
    except Exception as exception:
        return 'error', 'Connect server error: ' + str(exception)
    if ret.status_code == 401 or ret.status_code == 403:
        return 'error', 'Authenticate Error. Please make sure user and password are correct.'
    if ret.status_code == 200 and ret.json()['code'] == '2001':
        return 'success', 'created'

    print("status_code: {}, return text: {}".format(ret.status_code, ret.text))
    return 'error', 'Unexpected Error.'


def check_add_param(params):
    success = True
    required_params = ["repo", "branch", "scm_repo", "scm_branch", "version_control", "enabled"]
    miss_params = list()
    for param in required_params:
        if param not in params or not params[param]:
            miss_params.append(param)
            success = False
    if not success:
        print(
            "patch_tracking_cli add: error: the following arguments are required:  --{}".format(
                ", --".join(miss_params)
            )
        )
    return success


def add(args):
    """
    add tracking
    """
    style1 = bool(args.version_control) or bool(args.repo) or bool(args.branch) or bool(args.scm_repo) or bool(
        args.scm_branch
    ) or bool(args.enabled)
    style2 = bool(args.file)
    style3 = bool(args.dir)

    if str([style1, style2, style3]).count('True') >= 2:
        print("usage:" + add_usage)
        print("patch_tracking_cli add: error: mix different usage style")
        return

    if style2:
        file_input_track(args.file, args)
    elif style3:
        dir_input_track(args.dir, args)
    else:
        params = {
            'repo': args.repo,
            'branch': args.branch,
            'scm_repo': args.scm_repo,
            'scm_branch': args.scm_branch,
            'version_control': args.version_control,
            'enabled': args.enabled,
            'server': args.server,
            'user': args.user,
            'password': args.password
        }
        ret = params_input_track(params)
        if ret[0] == 'success':
            print('Tracking successfully.')
        else:
            print(ret[1])


def delete(args):
    """
    delete tracking
    """
    server = args.server
    user = args.user
    password = args.password

    err = latin1_encode(user)
    if err:
        print("ERROR: user: only latin1 character set are allowed.")
        return
    err = latin1_encode(password)
    if err:
        print("ERROR: password: Only latin1 character set are allowed.")
        return

    url = '/'.join(['https:/', server, 'tracking'])
    if args.branch:
        params = {'repo': args.repo, 'branch': args.branch}
    else:
        params = {'repo': args.repo}
    try:
        ret = requests.delete(url, params=params, verify=False, auth=HTTPBasicAuth(user, password))
        if ret.status_code == 200 and ret.json()['code'] == '2001':
            print('Tracking delete successfully.')
            return
        elif ret.status_code == 200 and ret.json()['code'] == '6005':
            print('Delete Nothing. Tracking not exist.')
            return

        print("Tracking delete failed. Error: {}".format(ret.text))
    except Exception as exception:
        print('Connect server error: ' + str(exception))


def query(args):
    """
    query table data
    """
    status, ret = query_table(args)
    if status == "success":
        df = pandas.DataFrame.from_dict(ret.json()["data"], orient="columns")
        df.index = range(1, len(df) + 1)
        print(df)
    else:
        print(ret)


def file_input_track(file_path, args):
    """
    load tracking from file
    """
    if os.path.exists(file_path) and os.path.isfile(file_path):
        if os.path.splitext(file_path)[-1] != ".yaml":
            print('Please input yaml file. Error in {}'.format(file_path))
            return
        with open(file_path) as file:
            content = file.readlines()
            params = dict()
            for item in content:
                if ":" in item:
                    k = item.split(':')[0]
                    value = item.split(':')[1].strip(' ').strip('\n')
                    params.update({k: value})
            params.update({'server': args.server, 'user': args.user, 'password': args.password})
            ret = params_input_track(params, file_path)
            if ret[0] == 'success':
                print('Tracking successfully {} for {}'.format(ret[1], file_path))
            else:
                print('Tracking failed for {}: {}'.format(file_path, ret[1]))
    else:
        print('yaml path error. Params error in {}'.format(file_path))


def dir_input_track(dir_path, args):
    """
    load tracking from dir
    """
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        dir_files = os.listdir(dir_path)
        if not dir_files:
            print('error: dir path empty')
            return
        for file in dir_files:
            if os.path.isfile(os.path.join(dir_path, file)) and os.path.splitext(file)[-1] == ".yaml":
                file_path = os.path.join(dir_path, file)
                file_input_track(file_path, args)
            else:
                print('Please input yaml file. Error in {}'.format(file))
    else:
        print('error: dir path error. Params error in {}'.format(dir_path))


parser = argparse.ArgumentParser(
    prog='patch_tracking_cli',
    allow_abbrev=False,
    description="command line tool for manipulating patch tracking information"
)
subparsers = parser.add_subparsers(description=None, dest='subparser_name', help='additional help')

# common argument
common_parser = argparse.ArgumentParser(add_help=False)
common_parser.add_argument("--server", required=True, help="patch tracking daemon server")

# authentication argument
authentication_parser = argparse.ArgumentParser(add_help=False)
authentication_parser.add_argument('--user', required=True, help='authentication username')
authentication_parser.add_argument('--password', required=True, help='authentication password')

# add
add_usage = """
    patch_tracking_cli add --server SERVER --user USER --password PASSWORD
                           --version_control github --scm_repo SCM_REPO --scm_branch SCM_BRANCH
                           --repo REPO --branch BRANCH --enabled True
    patch_tracking_cli add --server SERVER --user USER --password PASSWORD --file FILE
    patch_tracking_cli add --server SERVER --user USER --password PASSWORD --dir DIR"""
parser_add = subparsers.add_parser(
    'add', parents=[common_parser, authentication_parser], help="add tracking", usage=add_usage, allow_abbrev=False
)
parser_add.set_defaults(func=add)
parser_add.add_argument("--version_control", choices=['github'], help="upstream version control system")
parser_add.add_argument("--scm_repo", help="upstream scm repository")
parser_add.add_argument("--scm_branch", help="upstream scm branch")
parser_add.add_argument("--repo", help="source package repository")
parser_add.add_argument("--branch", help="source package branch")
parser_add.add_argument("--enabled", choices=["True", "true", "False", "false"], help="whether tracing is enabled")
parser_add.add_argument('--file', help='import patch tracking from file')
parser_add.add_argument('--dir', help='import patch tracking from files in directory')

# delete
parser_delete = subparsers.add_parser(
    'delete', parents=[common_parser, authentication_parser], help="delete tracking", allow_abbrev=False
)
parser_delete.set_defaults(func=delete)
parser_delete.add_argument("--repo", required=True, help="source package repository")
parser_delete.add_argument("--branch", help="source package branch")

# query
parser_query = subparsers.add_parser('query', parents=[common_parser], help="query tracking/issue", allow_abbrev=False)
parser_query.set_defaults(func=query)
parser_query.add_argument("--table", required=True, choices=["tracking", "issue"], help="query tracking or issue")
parser_query.add_argument("--repo", help="source package repository")
parser_query.add_argument("--branch", help="source package branch")


def main():
    args_ = parser.parse_args()
    if args_.subparser_name:
        if args_.func(args_) != "success":
            sys.exit(1)
        else:
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
