Name:           pkgship
Version:        1.1.0
Release:        2
Summary:        Pkgship implements rpm package dependence ,maintainer, patch query and so no.
License:        Mulan 2.0
URL:            https://gitee.com/openeuler/openEuler-Advisor
Source0:        https://gitee.com/openeuler/openEuler-Advisor/pkgship-%{version}.tar.gz

BuildArch:      noarch

BuildRequires: python3-flask-restful python3-flask python3 python3-pyyaml python3-sqlalchemy
BuildRequires: python3-prettytable python3-requests python3-flask-session python3-flask-script python3-marshmallow
BuildRequires: python3-Flask-APScheduler python3-pandas python3-retrying python3-xlrd python3-XlsxWriter
BuildRequires: python3-concurrent-log-handler
Requires: python3-pip python3-flask-restful python3-flask python3 python3-pyyaml
Requires: python3-sqlalchemy python3-prettytable python3-requests python3-concurrent-log-handler
Requires: python3-flask-session python3-flask-script python3-marshmallow python3-uWSGI
Requires: python3-pandas python3-dateutil python3-XlsxWriter python3-xlrd python3-Flask-APScheduler python3-retrying

%description
Pkgship implements rpm package dependence ,maintainer, patch query and so no.

%prep
%autosetup -n pkgship-%{version}

%build
%py3_build

%install
%py3_install


%check
# The apscheduler cannot catch the local time, so a time zone must be assigned before running the test case.
export TZ=Asia/Shanghai
# change log_path to solve default log_path permission denied problem
log_path=`pwd`/tmp/
sed -i "/\[LOG\]/a\log_path=$log_path" test/common_files/package.ini
%{__python3} -m unittest test/init_test.py
%{__python3} -m unittest test/read_test.py
%{__python3} -m unittest test/write_test.py
rm -rf $log_path

%post

%postun


%files
%doc README.md
%{python3_sitelib}/*
%config %{_sysconfdir}/pkgship/*
%attr(0755,root,root) %{_bindir}/pkgshipd
%attr(0755,root,root) %{_bindir}/pkgship

%changelog
* Tue Sep 1 2020 Zhengtang Gong <gongzhengtang@huawei.com> - 1.1.0-2
- Delete the packaged form of pyinstaller and change the execution
  of the command in the form of a single file as the input

* Sat Aug 29 2020 Yiru Wang <wangyiru1@huawei.com> - 1.1.0-1
- Add package management features:
  RPM packages statically displayed in the version repository
  RPM packages used time displayed for current version in the version repository
  Issue management of packages in a version-management repository

* Fri Aug 21 2020 Chengqiang Bao < baochengqiang1@huawei.com > - 1.0.0-7
- Fixed a problem with command line initialization of the Filepath parameter where relative paths are not supported and paths are too long

* Wed Aug 12 2020 Zhang Tao <zhangtao306@huawei.com> - 1.0.0-6
- Fix the test content to adapt to the new data structure, add BuildRequires for running %check

* Mon Aug 10 2020 Zhengtang Gong <gongzhengtang@huawei.com> - 1.0-5
- Command line supports calling remote services

* Wed Aug 5 2020 Yiru Wang <wangyiru1@huawei.com> - 1.0-4
- change Requires rpm pakcages' name to latest one

* Mon Jul 13 2020 Yiru Wang <wangyiru1@huawei.com> - 1.0-3
- run test cases while building

* Sat Jul 4 2020 Yiru Wang <wangyiru1@huawei.com> - 1.0-2
- cheange requires python3.7 to python3,add check pyinstaller file.

* Tue Jun 30 2020 Yiru Wang <wangyiru1@huawei.com> - 1.0-1
- add pkgshipd file

* Thu Jun 11 2020 Feng Hu <solar.hu@foxmail.com> - 1.0-0
- add macro to build cli bin when rpm install

* Sat Jun 6 2020 Feng Hu  <solar.hu@foxmail.com> - 1.0-0
- init package
