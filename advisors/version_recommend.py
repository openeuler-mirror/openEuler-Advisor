#!-*- coding:utf-8 -*-

import re
import datetime
import time
from typing import List

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

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns: None
        :raises: None
        """
        pass

    def latest_version(self, version_entry):
        """
        Get the latest version.

        :param version_entry: Package version list
        :returns: None
        :raises: None
        """
        version_entry.sort(reverse=True)
        return version_entry[0]

    def maintain_version(self, version_entry, current_version, pkg_type):
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

    def compare(self, z1, z2):
        """
        Get the max version.

        :param z1: The first version
        :param z2: The second version
        :returns 1: z1 great then z2
        :return -1: z2 great then z1
        :return 0: z1 equal then z2
        :raises: None
        """
        return self._compare(z1, z2)

    def _compare(self, z1, z2):
        """
        Get the max version.

        :param z1: The first version
        :param z2: The second version
        :returns 1: z1 great then z2
        :return -1: z2 great then z1
        :return 0: z1 equal then z2
        :raises: None
        """
        d1 = tuple(self._split(z1))  # 第一个参数版本号拆分,获取里面的数字/字母,得到序列
        d2 = tuple(self._split(z2))  # 第二个参数版本号拆分,获取里面的数字/字母,得到序列
        len1 = len(d1)
        len2 = len(d2)
        length = min(len1, len2)
        for index in range(length):
            if d1[index].isdigit() and d2[index].isdigit():
                if int(d1[index]) > int(d2[index]):
                    return 1
                elif int(d1[index]) < int(d2[index]):
                    return -1
            elif d1[index].isdigit():
                return 1
            elif d2[index].isdigit():
                return -1
            else:
                if d1[index] > d2[index]:
                    return 1
                elif d1[index] < d2[index]:
                    return -1
        if len1 > len2:
            return 1
        elif len1 < len2:
            return -1
        else:
            return 0

    def get_version_mode(self):
        """
        Get the version mode.

        :param: None
        :returns: Version type
        :raises: None
        """
        return self._version_type

    def _split(self, x):
        """
        Split the input args.

        :param x: Input args
        :returns: The split result
        :raises: None
        """
        for f, s in re.findall(r'([\d]+)|([^\d.-]+)', x):
            if f:
                float(f)
                yield f
            else:
                yield s


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
        xyz = version_digital[0:3]
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0:3] == version_temp[0:3]:  # 如果版本号与当前版本前三位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        if len(version_candidate) == 1:
            return '.'.join(version_candidate[0])

        w = '0'
        for version in version_candidate:
            if len(version) <= 3:
                continue

            if self._compare(version[3], w) > 0:
                w = version[3]

        xyz.append(w)
        return '.'.join(xyz)

    def latest_version(self, version_entry):
        """
        Get latest version.

        :param version_entry: Package version list
        :returns: latest version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]
        version_list = []
        for version in version_entry:
            version_list.append(re.split(r'[._-]', version))  # 将 version 拆分为列表,方便后续比较
        x = '0'
        for version in version_list:  # 第一轮比较取出最大的第一位
            if int(version[0]) > 1000: # consider it an useless exception
                continue

            if self._compare(x, version[0]) < 0:
                x = version[0]

        version_candidate = []
        for version in version_list:  # 将第一位最大的列入候选列表,准备第二位比较
            if x == version[0]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        version_list = version_candidate[:]
        y = '0'
        for version in version_list:  # 第二轮比较取出最大的第二位
            if len(version) <= 1:  # 过滤仅一位的版本号
                continue
            if self._compare(y, version[1]) < 0:
                y = version[1]

        version_candidate.clear()
        for version in version_list:  # 将第二位最大的列入候选列表,准备第三位比较
            if y == version[1]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        z = '0'
        version_list = version_candidate[:]
        for version in version_list:  # 第三轮比较取出最大的第三位
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if self._compare(z, version[2]) < 0:
                z = version[2]

        version_candidate.clear()
        for version in version_list:  # 最后一位最大版本必须惟一,直接返回结果
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if z == version[2]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        w = '0'
        version_list = version_candidate[:]
        for version in version_list:  # 最后一位最大版本必须惟一,直接返回结果
            if len(version) <= 3:  # 过滤仅三位的版本号
                continue
            if self._compare(w, version[3]) < 0:
                w = version[3]

        for version in version_list:  # 最后一位最大版本必须惟一,直接返回结果
            if len(version) <= 3:  # 过滤仅三位的版本号
                continue
            if w == version[3]:
                return '.'.join(version)

        return ''

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
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
        xy = version_digital[0:2]
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0:2] == version_temp[0:2]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        if len(version_candidate) == 1:
            return '.'.join(version_candidate[0])

        z = '0'
        for version in version_candidate:
            if len(version) <= 2:
                continue

            if self._compare(version[2], z) > 0:
                z = version[2]

        xy.append(z)
        return '.'.join(xy)

    def latest_version(self, version_entry):
        """
        Get latest version.

        :param version_entry: Package version list
        :returns: latest version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]
        version_list = []
        for version in version_entry:
            version_list.append(re.split(r'[._-]', version))  # 将 version 拆分为列表,方便后续比较
        x = '0'
        for version in version_list:  # 第一轮比较取出最大的第一位
            if int(version[0]) > 1000: # consider it an useless exception
                continue
            if self._compare(x, version[0]) < 0:
                x = version[0]

        version_candidate = []
        for version in version_list:  # 将第一位最大的列入候选列表,准备第二位比较
            if x == version[0]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        version_list = version_candidate[:]
        y = '0'
        for version in version_list:  # 第二轮比较取出最大的第二位
            if len(version) <= 1:  # 过滤仅一位的版本号
                continue
            if self._compare(y, version[1]) < 0:
                y = version[1]

        version_candidate.clear()
        for version in version_list:  # 将第二位最大的列入候选列表,准备第三位比较
            if y == version[1]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        z = '0'
        version_list = version_candidate[:]
        for version in version_list:  # 第三轮比较取出最大的第三位
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if self._compare(z, version[2]) < 0:
                z = version[2]

        for version in version_list:  # 最后一位最大版本必须惟一,直接返回结果
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if z == version[2]:
                return '.'.join(version)

        return ''

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
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

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'x.y'

    def latest_version(self, version_entry):
        """
        Get latest version.

        :param version_entry: Package version list
        :returns: latest version
        :raises: None
        """
        if len(version_entry) == 1:  # 仅一个版本,当前即为最新版本
            return version_entry[0]
        version_list = []
        for version in version_entry:
            version_list.append(re.split(r'[._-]', version))  # 将 version 拆分为列表,方便后续比较
        x = '0'
        for version in version_list:  # 第一轮比较取出最大的第一位
            if int(version[0]) > 1000: # consider it an useless exception
                continue

            if self._compare(x, version[0]) < 0:
                x = version[0]

        version_candidate = []
        for version in version_list:  # 将第一位最大的列入候选列表,准备第二位比较
            if x == version[0]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        version_list = version_candidate[:]
        y = '0'
        for version in version_list:  # 第二轮比较取出最大的第二位
            if len(version) <= 1:  # 过滤仅一位的版本号
                continue
            if self._compare(y, version[1]) < 0:
                y = version[1]

        version_candidate.clear()
        for version in version_list:  # x.y 版本类型中会小概率出现三位版本号,需要将第二位最大的列入候选列表,准备第三位比较
            if len(version) <= 1:  # 过滤仅一位的版本号
                continue
            if y == version[1]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        z = '0'
        version_list = version_candidate[:]
        for version in version_list:  # 第三轮比较取出最大的第三位
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if self._compare(z, version[2]) < 0:
                z = version[2]

        for version in version_list:  # 最后一位最大版本必须惟一,直接返回结果
            if len(version) <= 2:  # 过滤仅二位的版本号
                continue
            if z == version[2]:
                return '.'.join(version)

        return ''

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
        x = [version_digital[0]]
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0] == version_temp[0]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        if len(version_candidate) == 1:
            return '.'.join(version_candidate[0])

        y = '0'
        for version in version_candidate[0:]:
            if len(version) <= 1:
                continue

            if self._compare(version[1], y) > 0:
                y = version[1]
        x.append(y)
        return '.'.join(x)


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

    def latest_version(self, version_entry):
        """
        Get latest version.

        :param version_entry: Package version list
        :returns: latest version
        :raises: None
        """
        if 1 == len(version_entry):  # 仅一个版本,当前即为最新版本
            return version_entry[0]
        version_list: List[List[str]] = []
        for version in version_entry:
            version_list.append(re.split(r'[._-]', version))  # 将 version 拆分为列表,方便后续比较
        x = '0'
        for version in version_list:  # 第一轮比较取出最大的第一位
            if int(version[0]) > 1000: # consider it an useless exception
                continue

            if self._compare(x, version[0]) < 0:
                x = version[0]

        version_candidate = []
        for version in version_list:  # 将第一位最大的列入候选列表,准备第二位比较
            if x == version[0]:
                version_candidate.append(version)

        if len(version_candidate) == 1:  # 仅一个版本,候选即为最新版本
            return '.'.join(version_candidate[0])

        version_list = version_candidate[:]
        y = '0'
        for version in version_list:  # 第二轮比较取出最大的第二位
            if len(version) <= 1:  # 过滤仅一位的版本号
                continue
            if self._compare(y, version[1]) < 0:
                y = version[1]

        x.append(y)
        return '.'.join(x)

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
        x = [version_digital[0]]
        for version in version_entry:
            version_temp = re.split(r'[._-]', version)
            if version_digital[0] == version_temp[0]:  # 如果版本号与当前版本前两位一致，说明是维护分支版本
                version_candidate.append(version_temp)  # 将同特性版本的子版本挑选出来

        if len(version_candidate) == 1:
            return '.'.join(version_candidate[0])

        y = '0'
        for version in version_candidate[0:]:
            if len(version) <= 1:
                continue

            if self._compare(version[1], y) > 0:
                y = version[1]
        x.append(y)
        return '.'.join(x)

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
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

        if len(digital_list[1]) > 2:  # 第二位版本号不应该大于2位
            return False

        if str(int(digital_list[1])) != digital_list[1]:  # 版本类型为数字,且非0 开头
            return False

        if len(digital_list[2]) > 2:  # 第三位版本号不应该大于2位
            return False

        if str(int(digital_list[2])) != digital_list[2]:  # 版本类型为数字,且非0 开头
            return False

        return True

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
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

        :param None: No parameter
        :returns: None
        :raises: None
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

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'yyyyw'


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
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False

        if int(digital_list[1]) > 12 or int(digital_list[1]) == 0:  # 第二位为发布月份，小于12
            return False

        if int(digital_list[2]) > 31 or int(digital_list[2]) == 0:  # 第三位为发布日期，小于31
            return False

        # 判断日期是否为合法日期
        try:
            if '_' in version:
                d_time = time.mktime(time.strptime(version, "%Y_%m_%d"))
            elif '-' in version:
                d_time = time.mktime(time.strptime(version, "%Y-%m-%d"))
            elif '.' in version:
                d_time = time.mktime(time.strptime(version, "%Y.%m.%d"))
            else:
                return False

            now_str = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = time.mktime(time.strptime(now_str, '%Y-%m-%d'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            else:
                return True
        except ValueError as e:  # 时间格式非法
            _ = e
            print('Time foramt failed %s.', version)
            return False

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
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
        digital_list = re.split(r'[._-]', version)
        if len(digital_list) != 2:  # 通过 '.'分割后，应该剩下2位
            return False

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False
        year = int(digital_list[0])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        if int(digital_list[1]) > 12 or int(digital_list[1]) == 0:  # 第二位为发布月份，小于12
            return False

        if year == datetime.datetime.now().year and \
                int(digital_list[1]) > datetime.datetime.now().month:
            return False

        return True

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'yyyy.mm'


class VersionTypeYyyymm(VersionType):
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
        if len(version) != 6:  # 长度为6
            return False

        if not version.isdigit():  # 时间格式为数字
            return False

        digital_list = [version[0:4], version[4:]]

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False
        year = int(digital_list[0])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        if int(digital_list[1]) > 12 or int(digital_list[1]) == 0:  # 第二位为发布月份，小于12
            return False

        if year == datetime.datetime.now().year and \
                int(digital_list[1]) > datetime.datetime.now().month:
            return False

        return True

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'yyyymm'


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
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False

        if len(digital_list[0]) > 2:  # 第一位为主版本号，小于2位
            return False
        # 将年月拆分后分别判断
        if len(digital_list[1]) != 4:  # 年月等于4位
            return False
        year = str(digital_list[1][:2])
        month = str(digital_list[1][-2:])
        if year > str(datetime.datetime.now().year)[-2:]:  # 年份不能大于当前年份，不用考虑2000 年前的情况
            return False
        if month > '12' or month == '0':
            return False
        if len(digital_list[2]) > 2:  # 迭代号不大于2位
            return False
        return True

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'x.yymm.z'


class VersionTypeYyyymmdd(VersionType):
    """Version type Class for yyyymmdd"""

    def version_match(self, pkg_version):
        """
        Version match.

        :param pkg_version: Package version
        :returns True:  Version match success
        :returns False: version match fail
        :raises: None
        """
        version = pkg_version.strip()
        if len(version) != 8:  # 日期长度满足 8 位要求
            return False
        if not version.isdigit():  # 连续数字，没有其他分别符号
            return False
        digital_list = [version[:4], version[4:6], version[6:]]

        if int(digital_list[1]) > 12 or int(digital_list[1]) == 0:  # 第二位为发布月份，小于12
            return False

        if int(digital_list[2]) > 31 or int(digital_list[2]) == 0:  # 第三位为发布日期，小于31
            return False

        # 判断日期是否为合法日期
        try:
            d_time = time.mktime(time.strptime(version, "%Y%m%d"))
            now_str = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = time.mktime(time.strptime(now_str, '%Y-%m-%d'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            else:
                return True
        except ValueError as e:  # 时间格式非法
            _ = e
            print('Time format failed %s,', version)
            return False

    def __init__(self):
        """
        Initialize.

        :param None: No parameter
        :returns: None
        :raises: None
        """
        super().__init__()
        self._version_type = 'yyyymmdd'


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
        self.version_type = self._version_match(version_entry)
        if self.version_type is None:
            print('version type is None:', current_version)
            return

        print('version type = ', self.version_type.get_version_mode())
        self.latest_version = self._get_latest_version(version_entry)
        self.maintain_version = self._get_maintain_version(version_entry, current_version, pkg_type)

    def _version_match(self, version_entry):
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
                          VersionTypeYyyymm(): 0,
                          VersionTypeXYymmZ(): 0,
                          VersionTypeYyyymmdd(): 0}
        if not version_entry:
            return None
        for version in version_entry[:]:
            if not self._version_valid(version):
                version_entry.remove(version)  # 删除非法版本号
                continue
            for method, count in version_method.items():
                if method.version_match(version):
                    version_method[method] = count + 1

        # 解决多版本类型问题,选取类型最多的作为匹配,这个处理不是最优方案,需要改进
        method = max(version_method, key=lambda x: version_method[x])

        if version_method[method] == 0:
            return None
        else:
            return method

    @staticmethod
    def _version_valid(version):
        """
        Version valid check.

        :param version: The version of open source
        :returns True: valid version
        :returns False: invalid version
        :raises: None
        """
        m = re.match("^[0-9a-zA-Z._-]*$", version)
        if m is None:  # 版本号应该是 数字/小写字母/下划线/. 组成
            return False

        m = re.match('^[0-9].*', version)
        if m is None:  # 版本号应该是数字开头
            return False

        m = re.search(r'[ab]', version)
        if not m is None:
            return False

        if 'rc' in version \
                or 'RC' in version \
                or 'dev' in version \
                or 'beta' in version \
                or 'Beta' in version \
                or 'BETA' in version \
                or 'alpha' in version \
                or 'pl' in version \
                or 'pre' in version \
                or 'PRE' in version \
                or 'bp' in version:  # 仅获取正式版本
            return False

        if 'ubuntu' in version or 'fedora' in version:  # 去掉厂家专用版本号
            return False

        return True

    def _get_latest_version(self, version_entry):
        if self.version_type is None:
            return ''
        else:
            return self.version_type.latest_version(version_entry)

    def _get_maintain_version(self, version_entry, current_version, pkg_type):
        if self.version_type is None:
            return ''
        else:
            return self.version_type.maintain_version(version_entry, current_version, pkg_type)
