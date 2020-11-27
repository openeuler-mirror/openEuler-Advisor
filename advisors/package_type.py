#!/usr/bin/python3
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
The class of the package_type, used to get the package type of repo.
"""

import sys
import subprocess
import tempfile
from pyrpm.spec import Spec
from advisors import gitee


class PackageType:
    """Class for package type"""

    def __init__(self, repo):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        self.repo = repo
        self.pkg_type = self.get_pkg_type()

    @staticmethod
    def download_pkg(pkg_name, dir_name):
        """
        Download package.

        :param pkg_name: Package name
        :param dir_name: Package dir name
        :returns: Package path
        :raises: None
        """
        cmd_list = ['yumdownloader', '--destdir', dir_name, pkg_name]
        subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        if subp.wait() != 0:
            print("WARNING", "{cmd} > encount errors".format(cmd=" ".join(cmd_list)))
            return None

        return dir_name + '/' + "*.rpm"

    @staticmethod
    def delete_pkg(dir_name):
        """
        Delete package.

        :param dir_name: Package dir name
        :returns: None
        :raises: None
        """
        cmd_list = ['rm', '-rf', dir_name]
        subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        if subp.wait() != 0:
            print("WARNING", "{cmd} > encount errors".format(cmd=" ".join(cmd_list)))

    @staticmethod
    def get_lib_path(pkg_path):
        """
        Get library path.

        :param pkg_path: Package path
        :returns: library path of package
        :raises: None
        """
        cmd_list = ['rpm', '-ql', pkg_path]
        subp = subprocess.Popen(cmd_list, stdout=subprocess.PIPE)
        if subp.wait() != 0:
            print("WARNING", "{cmd} > encount errors".format(cmd=" ".join(cmd_list)))
            return None

        lib_path = []
        resp = subp.stdout.read().decode("utf-8")
        result = resp.splitlines()
        for line in result:
            if line.endswith('.so') or '.so.' in line:
                lib_path.append(line)
        return lib_path

    @property
    def _get_pkg_lib(self):
        """
        Get package library.

        :param None: None
        :returns: library path list of package
        :raises: None
        """
        try:
            user_gitee = gitee.Gitee()
        except NameError:
            sys.exit(1)
        spec_string = user_gitee.get_spec(self.repo)
        if not spec_string:
            print("WARNING: Spec of {pkg} can't be found on master".format(pkg=self.repo))
            return None

        lib_list = []
        spec_file = Spec.from_string(spec_string)
        with tempfile.TemporaryDirectory() as dir_name:
            for pkg_name in spec_file.packages_dict.keys():
                pkg_path = self.download_pkg(pkg_name, dir_name)
                if not pkg_path:
                    continue
                lib_path = self.get_lib_path(pkg_path)
                if lib_path:
                    lib_list.extend(lib_path)
                self.delete_pkg(pkg_path)
        return list(set(lib_list))

    def get_pkg_type(self):
        """
        Get package type,refer to
        https://gitee.com/openeuler/community/blob/master/zh/technical-committee/governance/software-management.md

        :param None: None
        :returns: Package type
        :raises: None
        """
        if 'python' in self.repo or 'perl' in self.repo:
            return 'app'

        if self.repo == 'gcc' or self.repo == 'kernel' or self.repo == 'glibc':
            return 'core'

        lib_list = self._get_pkg_lib
        if lib_list:
            return 'lib'

        return 'app'
