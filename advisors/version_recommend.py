#!/usr/bin/python3
import re
import datetime
import time

__ALL__ = ["VersionRecommend"]

class VersionType:
    def version_match(self, pkg_version):
        pass

    def latest_version(self, version_entry):
        version_entry.sort(reverse = True)
        return version_entry[0]

    def maintain_version(self, version_entry, current_version, pkg_type):
        return None

    def __init__(self):
        self._version_type = ''

    def get_version_mode(self):
        return self._version_type


class VersionType_x_y_z_w(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
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
        # todo 通过软件类型进一步选择版本号
        version_entry.sort(True)  # 将版本列表降序排序
        version_digital = re.split(r'[._]', current_version)  # 将版本号做拆分
        for version in version_entry:
            version_temp = re.split(r'[._]', version)
            if version_digital[0:2] == version_temp[0:2]:  # 如果版本号与当前版本前两位一致，说明是维护分支的最新版本
                return version
        return None

    def __init__(self):
        self._version_type = 'x.y.z.w'


class VersionType_x_y_z(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False
        if len(digital_list[0]) > 2:  # 第一位版本号不应该大于2位
            return False
        if len(digital_list[1]) > 2:  # 第二位版本号不应该大于2位
            return False
        if len(digital_list[2]) > 3:  # 第三位版本号不应该大于3位
            return False
        return True

    def maintain_version(self, version_entry, current_version, pkg_type):
        version_entry.sort(reverse = True)  # 将版本列表降序排序
        version_digital = re.split(r'[._]', current_version)  # 将版本号做拆分
        for version in version_entry:
            version_temp = re.split(r'[._]', version)
            if version_digital[0:2] == version_temp[0:2]:  # 如果版本号与当前版本前两位一致，说明是维护分支的最新版本
                return version
        return None

    def __init__(self):
        self._version_type = 'x.y.z'


class VersionType_x_y(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
        if len(digital_list) != 2:  # 通过 '.'分割后，应该剩下2位
            return False
        if len(digital_list[0]) > 2:  # 第一位版本号不应该大于2位
            return False
        if len(digital_list[1]) > 3:  # 第二位版本号不应该大于2位
            return False
        return True

    def __init__(self):
        self._version_type = 'x.y'


class VersionType_x(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
        if len(digital_list) != 1:  # 通过 '.'分割后，应该剩下1位
            return False
        if len(digital_list[0]) > 3:  # 第一位版本号不应该大于3位
            return False
        return True

    def __init__(self):
        self._version_type = 'x'


class VersionType_yyyy_x_y(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False

        if len(digital_list[0]) != 4:  # 第一位为发布年份，位数为4位
            return False
        year = int(digital_list[0])
        if year < 2000 or year > datetime.datetime.now().year:  # 软件发布时间应该大于2000 年，小于当前时间
            return False

        if len(digital_list[1]) > 2:  # 第二位版本号不应该大于2位
            return False

        if len(digital_list[2]) > 2:  # 第三位版本号不应该大于2位
            return False
        return True

    def __init__(self):
        self._version_type = 'yyyy.x.y'


class VersionType_yyyy_x(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
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
        self._version_type = 'yyyy.x'


class VersionType_yyyy_mm_dd(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
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
            else:
                d_time = time.mktime(time.strptime(version, "%Y.%m.%d"))

            now_str = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = time.mktime(time.strptime(now_str, '%Y-%m-%d'))
            if d_time > end_time:  # 判断日期是否大于当前日期
                return False
            else:
                return True
        except:  # 时间格式非法
            print('Time foramt failed %s.', version)
            return False

    def __init__(self):
        self._version_type = 'yyyy.mm.dd'


class VersionType_yyyy_mm(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
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
        self._version_type = 'yyyy.mm'


class VersionType_x_yymm_z(VersionType):
    def version_match(self, pkg_version):
        version = pkg_version.strip()
        digital_list = re.split(r'[._]', version)
        if len(digital_list) != 3:  # 通过 '.'分割后，应该剩下3位
            return False

        if len(digital_list[0]) > 2:  # 第一位为主版本号，小于2位
            return False
        # 将年月拆分后分别判断
        year = str(digital_list[1][:2])
        month = str(digital_list[1][-2:])
        if year > datetime.datetime.now().year[-2:]:  # 年份不能大于当前年份，不用考虑20000 年前的情况
            return False
        if month > 12 or month == 0:
            return False
        if len(digital_list[2]) > 2:  # 迭代号不大于2位
            return False
        return True

    def __init__(self):
        self._version_type = 'x.yymm.z'


class VersionType_yyyymmdd(VersionType):
    def version_match(self, pkg_version):
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
        except:  # 时间格式非法
            print('Time format failed %s,', version)
            return False

    def __init__(self):
        self._version_type = 'yyyymmdd'


class VersionRecommend:
    def __init__(self, version_entry, current_version, pkg_type):
        self.version_type = self._version_match(current_version)
        self.latest_version = self._get_latest_version(version_entry)
        self.maintain_version = self._get_maintain_version(version_entry, current_version, pkg_type)

    def _version_match(self, version):
        version_method = [VersionType_x_y_z_w(),
                          VersionType_x_y_z(),
                          VersionType_x_y(),
                          VersionType_x(),
                          VersionType_yyyy_x_y(),
                          VersionType_yyyy_x(),
                          VersionType_yyyy_mm_dd(),
                          VersionType_yyyy_mm(),
                          VersionType_x_yymm_z(),
                          VersionType_yyyymmdd()]

        for method in version_method:
            if method.version_match(version):
                print(version, method.get_version_mode())
                return method

    def _get_latest_version(self, version_entry):
        return self.version_type.latest_version(version_entry)

    def _get_maintain_version(self, version_entry, current_version, pkg_type):
        return self.version_type.maintain_version(version_entry, current_version, pkg_type)



if __name__ == '__main__':
    version_recommend = VersionRecommend(['1.2.3','1.2.4','1.3.0','2.0.1'],'1.2.3',0)
    print(version_recommend.latest_version)
    print(version_recommend.maintain_version)
