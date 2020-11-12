# !/usr/bin/python3
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
This is an test script for get url from repo name
"""
from advisors import version_recommend

X_Y_Z_W_VERSION_LIST = ["1.1.1.2", "1.1.1.3", "1.1.2.1", "1.1.2.2", "1.1.2.2.1", "2.1"]
X_Y_Z_VERSION_LIST = ["1.1", "1.1.1", "1.1.2", "1.1.3", "1.2", "1.2.1", "2.1"]
X_Y_VERSION_LIST = ["1", "1.2", "1.2.1", "1.3", "1.3.1", "2.0", "2.1", "3"]
X_VERSION_LIST = ["1", "2", "3", "3.1", "4", "5", "5.1"]
YYYY_X_Y_VERSION_LIST = ["2020.1.2", "2020.1.3", "2020.1.4", "2020.2.1", "2020.3.1", "2020.4.1"]
YYYY_X_VERSION_LIST = ["2020.1", "2020.2", "2020.6", "2020.7", "2020.13", "2020.20"]
YYYY_W_VERSION_LIST = ["2020.1", "2020.2", "2020.3", "2020.4", "2020.5", "2020.6", "2020.15"]
YYYY_MM_DD_VERSION_LIST = ["2020.1.1", "2020.2.3", "2020.4.6", "2020.5.30"]
YYYYMMDD_VERSION_LIST = ["20200101", "20200203", "20200406", "20200530"]
X_YY_MM_Z_VERSION_LIST = ["1.20.02.5", "1.20.03.1", "1.20.04.5", "1.20.05.1", "1.20.06.3"]


def test_version_type_xyzw():
    """
    Test xyzw verison type
    """
    version_type = version_recommend.VersionTypeXYZW()
    maintain_version = version_type.maintain_version(X_Y_Z_W_VERSION_LIST,
                                                     X_Y_Z_W_VERSION_LIST[2], 0)
    assert maintain_version == "1.1.2.2.1"

    latest_version = version_type.latest_version(X_Y_Z_W_VERSION_LIST)
    assert latest_version == "2.1"


def test_version_type_xyz():
    """
    Test xyz verison type
    """
    version_type = version_recommend.VersionTypeXYZ()
    maintain_version = version_type.maintain_version(X_Y_Z_VERSION_LIST,
                                                     X_Y_Z_VERSION_LIST[2], 0)
    assert maintain_version == "1.1.3"

    latest_version = version_type.latest_version(X_Y_Z_VERSION_LIST)
    assert latest_version == "2.1"


def test_version_type_xy():
    """
    Test xy verison type
    """
    version_type = version_recommend.VersionTypeXY()
    maintain_version = version_type.maintain_version(X_Y_VERSION_LIST, X_Y_VERSION_LIST[2], 0)
    assert maintain_version == "1.3.1"

    latest_version = version_type.latest_version(X_Y_VERSION_LIST)
    assert latest_version == "3"


def test_version_type_x():
    """
    Test x verison type
    """
    version_type = version_recommend.VersionTypeX()
    maintain_version = version_type.maintain_version(X_VERSION_LIST, X_VERSION_LIST[2], 0)
    assert maintain_version == "3.1"

    latest_version = version_type.latest_version(X_VERSION_LIST)
    assert latest_version == "5.1"


def test_version_type_yyyyxy():
    """
    Test yyyyxy verison type
    """
    version_type = version_recommend.VersionTypeYyyyXY()
    maintain_version = version_type.maintain_version(YYYY_X_Y_VERSION_LIST,
                                                     YYYY_X_Y_VERSION_LIST[2], 0)
    assert maintain_version == "2020.1.4"

    latest_version = version_type.latest_version(YYYY_X_Y_VERSION_LIST)
    assert latest_version == "2020.4.1"


def test_version_type_yyyyx():
    """
    Test yyyyx verison type
    """
    version_type = version_recommend.VersionTypeYyyyXY()
    maintain_version = version_type.maintain_version(YYYY_X_VERSION_LIST, YYYY_X_VERSION_LIST[2], 0)
    assert maintain_version == "2020.6"

    latest_version = version_type.latest_version(YYYY_X_VERSION_LIST)
    assert latest_version == "2020.20"


def test_version_type_yyyyw():
    """
    Test yyyyw verison type
    """
    version_type = version_recommend.VersionTypeYyyyW()
    maintain_version = version_type.maintain_version(YYYY_W_VERSION_LIST, YYYY_W_VERSION_LIST[2], 0)
    assert maintain_version == "2020.3"

    latest_version = version_type.latest_version(YYYY_W_VERSION_LIST)
    assert latest_version == "2020.15"


def test_version_type_yyyymmdd():
    """
    Test yyyy.mm.dd verison type
    """
    version_type = version_recommend.VersionTypeYyyyMmDd()
    maintain_version = version_type.maintain_version(YYYYMMDD_VERSION_LIST,
                                                     YYYYMMDD_VERSION_LIST[2],
                                                     0)
    assert maintain_version == "20200406"

    latest_version = version_type.latest_version(YYYYMMDD_VERSION_LIST)
    assert latest_version == "20200530"


def test_version_type_yyyymmdd_sparator_1():
    """
    Test yyyymmdd verison type
    """
    version_type = version_recommend.VersionTypeYyyyMmDd()
    maintain_version = version_type.maintain_version(YYYY_MM_DD_VERSION_LIST,
                                                     YYYY_MM_DD_VERSION_LIST[2], 0)
    assert maintain_version == "2020.4.6"

    latest_version = version_type.latest_version(YYYY_MM_DD_VERSION_LIST)
    assert latest_version == "2020.5.30"


def test_version_type_xyymmz():
    """
    Test xyymmz verison type
    """
    version_type = version_recommend.VersionTypeYyyyMmDd()
    maintain_version = version_type.maintain_version(X_YY_MM_Z_VERSION_LIST,
                                                     X_YY_MM_Z_VERSION_LIST[2],
                                                     0)
    assert maintain_version == "1.20.04.5"

    latest_version = version_type.latest_version(X_YY_MM_Z_VERSION_LIST)
    assert latest_version == "1.20.06.3"


def test_version_type_libsrtp():
    """
    Test libsrtp
    """
    tags = ['1', '1.5', '1.5.0', '1.5.1', '1.5.2', '1.5.3', '1.5.4', '1.6', '1.6.0', '2',
            '2.0', '2.0.0', '2.1', '2.1.0', '2.2', '2.2.0', '2.3', '2.3.0']
    current_version = "1.5.2"
    version_type = version_recommend.VersionRecommend(tags, current_version, 0)
    assert version_type.latest_version == '2.3.0'
    assert version_type.maintain_version == '1.5.4'


def test_version_type_pkgconf():
    """
    Test pkgconf
    """
    tags = ['0.1', '0.1.1', '0.2', '0.3', '0.4', '0.5', '0.5.1', '0.5.2', '0.5.3', '0.6',
            '0.7', '0.8', '0.8.1', '0.8.10', '0.8.11', '0.8.12', '0.8.2', '0.8.3', '0.8.4',
            '0.8.5', '0.8.6', '0.8.7', '0.8.8', '0.8.9', '0.9.0', '0.9.1', '0.9.10', '0.9.11',
            '0.9.12', '0.9.2', '0.9.3', '0.9.4', '0.9.5', '0.9.6', '0.9.7', '0.9.8', '0.9.9',
            '1', '1.0.1', '1.0.2', '1.1.0', '1.1.1', '1.2.0', '1.2.1', '1.2.2', '1.3.0', '1.3.1',
            '1.3.10', '1.3.11', '1.3.12', '1.3.2', '1.3.3', '1.3.4', '1.3.5', '1.3.6', '1.3.7',
            '1.3.8', '1.3.9', '1.3.90', '1.4.0', '1.4.1', '1.4.2', '1.5.1', '1.5.2', '1.5.3',
            '1.5.4', '1.6.0', '1.6.1', '1.6.2', '1.6.3', '1.7.0', '1.7.1', '1.7.2', '1.7.3']

    current_version = "1.7.3"
    version_type = version_recommend.VersionRecommend(tags, current_version, 0)
    assert version_type.latest_version == '1.7.3'
    assert version_type.maintain_version == '1.7.3'


def test_version_type_mksh():
    """
    Test mksh
    """
    tags = ['19', '20', '21', '22', '23', '24', '24b', '24c', '25', '26', '26b', '26c',
            '27', '27d', '27e', '28', '29', '29b', '29c', '29d', '29e', '29f', '29g',
            '30', '31', '31b', '31c', '31d', '32', '33', '33b', '33c', '33d', '35', '35b',
            '36', '36b', '37', '37b', '37c', '38', '38b', '38c', '39', '39b', '39c',
            '40', '40b', '40c', '40d', '40e', '40f', '41', '41b', '41c', '42', '42b',
            '43', '44', '45', '46', '47', '48', '48b', '49', '50', '50b', '50c',
            '50d', '50e', '50f', '51', '52', '52b', '52c', '53', '53a', '54', '55',
            '56', '56b', '56c', '57', '58', '59', '59b', '59c']

    current_version = "56c"
    version_type = version_recommend.VersionRecommend(tags, current_version, 0)
    assert version_type.latest_version == '59'
    assert version_type.maintain_version == '56c'


def test_version_type_pyxattr():
    """
    Test pyxattr
    """
    tags = ['0.1', '0.2.1', '0.2.2', '0.3.0', '0.4.0', '0.5.0', '0.7.0', '0.7.1']

    current_version = "0.6.1"
    version_type = version_recommend.VersionRecommend(tags, current_version, 0)
    assert version_type.latest_version == '0.7.1'
    assert version_type.maintain_version == '0.6.1'
