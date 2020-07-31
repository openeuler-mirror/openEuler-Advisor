"""
setup about building of pactch tracking
"""
import setuptools

setuptools.setup(
    name='patch-tracking',
    version='1.0.0',
    packages=setuptools.find_packages(),
    url='https://openeuler.org/zh/',
    license='Mulan PSL v2',
    author='ChenYanpan',
    author_email='chenyanpan@huawei.com',
    description='This is a tool for automatically tracking upstream repository code patches',
    requires=['requests', 'flask', 'flask_restx', 'Flask_SQLAlchemy', 'Flask_APScheduler'],
    data_files=[
        ('/etc/patch-tracking/', ['patch_tracking/settings.conf']),
        ('/etc/patch-tracking/', ['patch_tracking/logging.conf']),
        ('/var/patch-tracking/', ['patch_tracking/db.sqlite']),
        ('/usr/bin/', ['patch_tracking/cli/patch-tracking-cli']),
        ('/usr/bin/', ['patch_tracking/patch-tracking']),
        ('/usr/bin/', ['patch_tracking/cli/generate_password']),
        ('/usr/lib/systemd/system/', ['patch_tracking/patch-tracking.service']),
    ],
)
