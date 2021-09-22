#!/usr/bin/python3
"""
Package management program installation configuration
file for openEuler-Advisor
"""
from distutils.core import setup


setup(
    name='openEuler-Advisor',
    version='1.0.1',
    py_modules=[
        'advisors.simple_update_robot',
        'advisors.build_rpm_package',
        'advisors.oa_upgradable',
        'advisors.package_type',
        'advisors.check_upstream',
        'advisors.version_recommend',
        'advisors.match_patches',
        'advisors.check_missing_file',
        'advisors.check_repeated_repo',
        'advisors.check_source_url',
        'advisors.create_repo',
        'advisors.check_abi',
        'advisors.check_conf',
        'advisors.check_command',
        'advisors.create_repo_with_srpm',
        'advisors.psrtool',
        'advisors.check_version',
        'advisors.review_tool',
        'advisors.tc_reminder',
        'advisors.which_archived',
        'advisors.yaml2url',
        'advisors.gitee',
        'legacy.python-packager',
        'legacy.who_maintain',
        'legacy.tc_statistic',
        'tests.test_yaml2url'],
    requires=['python_rpm_spec (>=0.10)',
              'PyYAML (>=5.3.1)',
              'requests (>=2.24.0)',
              'rpmdevtools (>=8.3)',
              'bs4 (>=0.0.1)',
              'yum_utils (>=1.1.31)'],
    license='Mulan PSL v2',
    platforms=["all"],
    url='https://gitee.com/openeuler/openEuler-Advisor',
    author='licihua',
    author_email='licihua@huawei.com',
    maintainer='licihua',
    maintainer_email='licihua@huawei.com',
    description='collection of automatic tools for easily maintaining openEuler',
    data_files=[
        ('/usr/bin/', ['command/simple_update_robot']),
        ('/usr/bin/', ['command/oa_upgradable']),
        ('/usr/bin/', ['command/check_missing_file']),
        ('/usr/bin/', ['command/check_repeated_repo']),
        ('/usr/bin/', ['command/check_source_url']),
        ('/usr/bin/', ['command/check_version']),
        ('/usr/bin/', ['command/create_repo']),
        ('/usr/bin/', ['command/create_repo_with_srpm']),
        ('/usr/bin/', ['command/psrtool']),
        ('/usr/bin/', ['command/review_tool']),
        ('/usr/bin/', ['command/tc_reminder']),
        ('/usr/bin/', ['command/which_archived']),
        ('/usr/bin/', ['prow/prow_review_tool'])]
)
