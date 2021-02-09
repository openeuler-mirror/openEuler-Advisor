#!/usr/bin/env python3
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
This is an module for version recommend
"""
import datetime
import re
import time

__ALL__ = ["VersionRecommend"]

"""

The base class of the version recommend, used to get the latest version and maintain version.

"""


class VersionType(object):
    """Base class for version recommend"""

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        self._version_type = None
        self._separator = '.'

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns: None
        :raises: None
        """

    def latest_version(self, version_entry):
        """
        Get the latest version.

        :param version_entry: Package version list
        :returns: latest version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]
        version_list = []
        for version in version_entry:
            version_list.append(re.split(r'[._-]', version))  # 将 version 拆分为列表,方便后续比较

        version = self.get_latest_version(version_list, 0)
        return self._separator.join(version)

    @staticmethod
    def maintain_version(version_entry, current_version, pkg_type):
        """
        Get the maintain version.

        :param version_entry: Package version list
        :param current_version: Current version
        :param pkg_type: Package type
        :returns : Maintain version
        :raises: None
        """
        _ = version_entry, pkg_type
        return current_version

    def compare(self, _z1, _z2):
        """
        Get the max version.

        :param _z1: The first version
        :param _z2: The second version
        :returns 1: _z1 great then _z2
        :return -1: _z2 great then _z1
        :return 0: _z1 equal then _z2
        :raises: None
        """
        return self._compare(_z1, _z2)

    def _compare(self, _z1, _z2):
        """
        Get the max version.

        :param version_z1: The first version
        :param version_z2: The second version
        :returns 1: version_z1 great then version_version_z2
        :return -1: version_z2 great then version_z1
        :return 0: version_z1 equal then version_version_z2
        :raises: None
        """
        result = 0
        _d1 = tuple(self._split(_z1))  # 第一个参数版本号拆分,获取里面的数字/字母,得到序列
        _d2 = tuple(self._split(_z2))  # 第二个参数版本号拆分,获取里面的数字/字母,得到序列
        len1 = len(_d1)
        len2 = len(_d2)
        length = min(len1, len2)
        for index in range(length):
            if _d1[index].isdigit() and _d2[index].isdigit():
                if int(_d1[index]) > int(_d2[index]):
                    result = 1
                    break
                if int(_d1[index]) < int(_d2[index]):
                    result = -1
                    break

            if _d1[index].isdigit():
                result = 1
                break

            if _d2[index].isdigit():
                result = -1
                break

            if _d1[index] > _d2[index]:
                result = 1
                break

            if _d1[index] < _d2[index]:
                result = -1
                break

        if result != 0:
            return result

        if len1 > len2:
            result = 1

        if len1 < len2:
            result = -1

        return result

    def get_version_mode(self):
        """
        Get the version mode.

        :param: None
        :returns: Version type
        :raises: None
        """
        return self._version_type

    @staticmethod
    def _split(data):
        """
        Split the input args.

        :param data: Input args
        :returns: The split result
        :raises: None
        """
        for _f, _s in re.findall(r'([\d]+)|([^\d.-]+)', data):
            if _f:
                float(_f)
                yield _f
            else:
                yield _s

    def get_latest_version(self, version_list, start):
        """
        Get the latest version.
        """
        if not version_list:
            return ''

        index = start
        version_candidate = version_list[:]
        while True:
            version_entry = version_candidate[:]
            version_candidate.clear()
            _y = '0'
            for version in version_entry:

                if len(version) <= index:
                    continue

                if self._compare(_y, version[index]) < 0:
                    _y = version[index]

            for version in version_entry:
                if len(version) <= index:
                    continue

                if _y == version[index]:
                    version_candidate.append(version)

            if not version_candidate:
                return version_entry[0]

            if len(version_candidate) == 1:
                return version_candidate[0]

            index = index + 1


class VersionTypeXYZW(VersionType):
    """Version type Class for x.y.z.w"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 4:  # 通过 '.'分割后，应该剩下4位
            return False
        if len(digital_list[0]) > 2:  # 第一位版本号不应该大于2位
            return False
        if len(digital_list[1]) > 2:  # 第二位版本号不应该大于2位
            return False
        if len(digital_list[2]) > 3:  # 第三位版本号不应该大于3位
            return False
        if len(digital_list[3]) > 1:  # 第四位版本号不应该大于1位
            return False
        return True

    def maintain_version(self, version_entry, current_version, pkg_type):
        """
        Get the maintain version.

        :param version_entry: Package version list
        :param current_version: Current version
        :param pkg_type: Package type
        :returns : Maintain version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]

        version_candidate = []
        version_digital = re.split(r'[._-]', current_version)  # 将版本号做拆分
        if len(version_entry) <= 1:  # 如果当前版本号仅一位，不能判断维护版本号
            return self._separator.join(version_digital)

        version_digital = re.split(r'[._-]', current_version)  # 将版本号做拆分
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0:3] == version_temp[0:3]:  # 如果版本号与当前版本前三位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        version = self.get_latest_version(version_candidate, 3)
        if version:
            return self._separator.join(version)

        return current_version

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'x.y.z.w'


class VersionTypeXYZ(VersionType):
    """Version type Class for x.y.z"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False
        if len(digital_list[0]) > 2:  # 第一位版本号不应该大于2位
            return False
        if len(digital_list[1]) > 3:  # 第二位版本号不应该大于3位
            return False
        if len(digital_list[2]) > 3:  # 第三位版本号不应该大于3位
            return False
        return True

    def maintain_version(self, version_entry, current_version, pkg_type):
        """
        Get the maintain version.

        :param version_entry: Package version list
        :param current_version: Current version
        :param pkg_type: Package type
        :returns : Maintain version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]

        version_candidate = []
        version_digital = re.split(r'[._-]', current_version)  # 将版本号做拆分
        if len(version_entry) <= 1:  # 如果当前版本号仅一位，不能判断维护版本号
            return self._separator.join(version_digital)

        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0:2] == version_temp[0:2]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        version = self.get_latest_version(version_candidate, 2)
        if version:
            return self._separator.join(version)
        return current_version

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'x.y.z'


class VersionTypeXY(VersionType):
    """Version type Class for x.y"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 2:  # 通过 '.'分割后，应该剩下2位
            return False
        if len(digital_list[0]) > 2:  # 第一位版本号不应该大于2位
            return False
        if len(digital_list[1]) > 3:  # 第二位版本号不应该大于2位
            return False
        return True

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'x.y'

    def maintain_version(self, version_entry, current_version, pkg_type):
        """
        Get the maintain version.

        :param version_entry: Package version list
        :param current_version: Current version
        :param pkg_type: Package type
        :returns : Maintain version
        :raises: None
        """
        version_candidate = []
        version_digital = re.split(r'[._-]', current_version)  # 将版本号做拆分
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0] == version_temp[0]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        version = self.get_latest_version(version_candidate, 1)
        if version:
            return self._separator.join(version)
        return current_version


class VersionTypeX(VersionType):
    """Version type Class for x"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 1:  # 通过 '.'分割后，应该剩下1位
            return False
        if len(digital_list[0]) > 3:  # 第一位版本号不应该大于3位
            return False
        return True

    def maintain_version(self, version_entry, current_version, pkg_type):
        """
        Get the maintain version.

        :param version_entry: Package version list
        :param current_version: Current version
        :param pkg_type: Package type
        :returns : Maintain version
        :raises: None
        """
        version_candidate = []
        version_digital = re.split(r'[._-]', current_version)  # 将版本号做拆分
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0] == version_temp[0]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        version = self.get_latest_version(version_candidate, 1)
        if version:
            return self._separator.join(version)
        return current_version

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'x'


class VersionTypeYyyyXY(VersionType):
    """Version type Class for yyyy.x.y"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False

        year = int(digital_list[0])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        if len(digital_list[1]) > 2 or \
                str(int(digital_list[1])) != digital_list[1]:  # 第二位版本号不应该大于2位
            return False

        if len(digital_list[2]) > 2 or \
                str(int(digital_list[2])) != digital_list[2]:  # 第三位版本号不应该大于2位
            return False

        return True

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'yyyy.x.y'


class VersionTypeYyyyX(VersionType):
    """Version type Class for yyyy.x"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 2:  # 通过 '.'分割后，应该剩下2位
            return False

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False
        year = int(digital_list[0])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        if len(digital_list[1]) > 2:  # 第二位版本号不应该大于2位
            return False
        return True

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'yyyy.x'


class VersionTypeYyyyW(VersionType):
    """Version type Class for yyyyw"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        if len(version) != 5:  # 共5 位
            return False
        if not str(version[0:4]).isdigit():  # 前四位为年份数字
            return False

        year = int(version[0:4])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        return True

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'yyyyw'
        self.separation = ""


class VersionTypeYyyyMmDd(VersionType):
    """Version type Class for yyyy.mm.dd"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        # 判断日期是否为合法日期
        try:
            if '_' in version:
                d_time = time.mktime(time.strptime(version, "%Y_%m_%d"))
                self._separator = '_'
            elif '-' in version:
                d_time = time.mktime(time.strptime(version, "%Y-%m-%d"))
                self._separator = '-'
            elif '.' in version:
                d_time = time.mktime(time.strptime(version, "%Y.%m.%d"))
                self._separator = '.'
            else:
                d_time = time.mktime(time.strptime(version, "%Y%m%d"))
                self._separator = ''

            now_str = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = time.mktime(time.strptime(now_str, '%Y-%m-%d'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            return True
        except ValueError as error:  # 时间格式非法
            _ = error
            return False

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'yyyy.mm.dd'


class VersionTypeYyyyMm(VersionType):
    """Version type Class for yyyy.mm"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        try:
            if '_' in version:
                d_time = time.mktime(time.strptime(version, "%Y_%m"))
                self._separator = '_'
            elif '-' in version:
                d_time = time.mktime(time.strptime(version, "%Y-%m"))
                self._separator = '-'
            elif '.' in version:
                d_time = time.mktime(time.strptime(version, "%Y.%m"))
                self._separator = '.'
            else:
                d_time = time.mktime(time.strptime(version, "%Y%m"))
                self._separator = ''

            now_str = datetime.datetime.now().strftime('%Y-%m')
            end_time = time.mktime(time.strptime(now_str, '%Y-%m'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            return True
        except ValueError as error:  # 时间格式非法
            print('Time foramt failed %s.', version, error)
            return False

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'yyyy.mm'
        self.separation = ""


class VersionTypeXYymmZ(VersionType):
    """Version type Class for x.yymm.z"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 3 or \
                len(digital_list[0]) > 2 or \
                len(digital_list[1]) != 4 or \
                len(digital_list[2]) > 2:
            return False

        try:
            d_time = time.mktime(time.strptime(digital_list[1], "%y%m"))
            self._separator = ''
            now_str = datetime.datetime.now().strftime('%y-%m')
            end_time = time.mktime(time.strptime(now_str, '%y-%m'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            return True
        except ValueError as __:  # 时间格式非法
            return False

    def __init__(self):
        """
        Initialize.
        """
        super().__init__()
        self._version_type = 'x.yymm.z'


class VersionRecommend(object):
    """Version recommend Class for open source"""

    def __init__(self, version_entry, current_version, pkg_type):
        """
        Initialize.

        :param version_entry: The version list of open source
        :param current_version: The current version  of open source
        :returns: None
        :raises: None
        """
        self.latest_version = current_version  # 提供初值,避免 current_version 为空导致后面出现异常
        self.maintain_version = current_version
        self.version_type = self.version_match(version_entry)
        if self.version_type is None:
            print('version type is None:', current_version)
            return

        print('version type = ', self.version_type.get_version_mode())
        self.latest_version = self._get_latest_version(version_entry)
        self.maintain_version = self._get_maintain_version(version_entry, current_version, pkg_type)

    def version_match(self, version_entry):
        """
        Version match function.

        :param version_entry: The version list of open source
        :returns: The method input version list
        :raises: None
        """
        version_method = {VersionTypeXYZW(): 0,
                          VersionTypeXYZ(): 0,
                          VersionTypeXY(): 0,
                          VersionTypeX(): 0,
                          VersionTypeYyyyXY(): 0,
                          VersionTypeYyyyX(): 0,
                          VersionTypeYyyyW(): 0,
                          VersionTypeYyyyMmDd(): 0,
                          VersionTypeXYymmZ(): 0
                          }
        if not version_entry:
            return None
        for version in version_entry[:]:
            if not self.version_valid(version):
                version_entry.remove(version)  # 删除非法版本号
                continue
            for method, count in version_method.items():
                if method.version_match(version):
                    version_method[method] = count + 1

        # 解决多版本类型问题,选取类型最多的作为匹配,这个处理不是最优方案,需要改进
        method = max(version_method, key=lambda _x: version_method[_x])
        if version_method[method] == 0:
            return None

        return method

    @staticmethod
    def version_valid(version):
        """
        Version valid check.

        :param version: The version of open source
        :returns True: valid version
        :returns False: invalid version
        :raises: None
        """
        _m = re.match("^[0-9a-zA-Z._-]*$", version)
        if _m is None:  # 版本号应该是 数字/小写字母/下划线/. 组成
            return False

        _m = re.match('^[0-9].*', version)
        if _m is None:  # 版本号应该是数字开头
            return False

        # autoconf213 https://git.savannah.gnu.org/git/autoconf.git  
        _m = re.search(r'[abcd]', version)
        if not _m is None:
            return False

        # CR:  https://github.com/picketbox/commons/releases/tag/ '1.0.0.CR1'
        # PRE: https://svn.code.sf.net/p/openjade/code/tags  'jade_1_3_pre1'
        # RC:  https://github.com/dbry/WavPack.git/tags  '4.75.0-rc'
        # ALPHA： https://github.com/dbry/WavPack.git/tags  '4.60.0-alpha'
        # BP: https://git.openldap.org/openldap/openldap/-/tags  '2.1.BP'
        # DEV: https://github.com/moby/libnetwork/tags '0.8.0-dev.1'
        # PL:  https://github.com/HewlettPackard/netperf/tags 'netperf-2.2pl2'

        ill_version_list = ['CR', 'RC', 'DEV',
                            'BETA', 'ALPHA', 'PL', 'PRE', 'BP']
        for ill_version in ill_version_list:
            if ill_version in version.upper():
                return False

        if 'ubuntu' in version or 'fedora' in version:  # 去掉厂家专用版本号
            return False

        return True

    def _get_latest_version(self, version_entry):
        if not version_entry:
            return ''
        if not self.version_type:
            return ''
        return self.version_type.latest_version(version_entry)

    def _get_maintain_version(self, version_entry, current_version, pkg_type):
        if not version_entry:
            return ''
        if self.version_type is None:
            return ''
        return self.version_type.maintain_version(version_entry, current_version, pkg_type)
