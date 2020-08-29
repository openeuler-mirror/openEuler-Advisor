#!/usr/bin/python3
"""
Package management program installation configuration
file for software packaging
"""
from distutils.core import setup


config_path = "/etc/pkgship/"  # pylint: disable=invalid-name

setup(
    name='packageship',
    version='1.0',
    py_modules=[
        'packageship.application.__init__',
        'packageship.application.app_global',
        'packageship.application.apps.__init__',
        'packageship.application.apps.package.serialize',
        'packageship.application.apps.package.url',
        'packageship.application.apps.package.view',
        'packageship.application.apps.package.function.be_depend',
        'packageship.application.apps.package.function.build_depend',
        'packageship.application.apps.package.function.constants',
        'packageship.application.apps.package.function.install_depend',
        'packageship.application.apps.package.function.packages',
        'packageship.application.apps.package.function.searchdb',
        'packageship.application.apps.package.function.self_depend',
        'packageship.application.apps.lifecycle.function.base',
        'packageship.application.apps.lifecycle.function.download_yaml',
        'packageship.application.apps.lifecycle.function.gitee',
        'packageship.application.apps.lifecycle.function.concurrent',
        'packageship.application.apps.lifecycle.serialize',
        'packageship.application.apps.lifecycle.url',
        'packageship.application.apps.lifecycle.view',
        'packageship.application.initsystem.data_import',
        'packageship.application.models.package',
        'packageship.application.settings',
        'packageship.libs.__init__',
        'packageship.libs.configutils.readconfig',
        'packageship.libs.dbutils.sqlalchemy_helper',
        'packageship.libs.exception.ext',
        'packageship.libs.log.loghelper',
        'packageship.manage',
        'packageship.pkgship',
        'packageship.selfpkg',
        'packageship.system_config'],
    requires=['prettytable (==0.7.2)',
              'Flask_RESTful (==0.3.8)',
              'Flask_Session (==0.3.1)',
              'Flask_Script (==2.0.6)',
              'Flask (==1.1.2)',
              'marshmallow (==3.5.1)',
              'SQLAlchemy (==1.3.16)',
              'PyYAML (==5.3.1)',
              'requests (==2.21.0)',
              'pyinstall (==0.1.4)',
              'uwsgi (==2.0.18)'],
    license='Dependency package management',
    long_description=open('README.md', encoding='utf-8').read(),
    author='gongzt',
    data_files=[
        (config_path, ['packageship/package.ini']),
        ('/usr/bin', ['packageship/pkgshipd'])]
)
