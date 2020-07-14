Name:           pkgship
Version:        1.0
Release:        3
Summary:        Pkgship implements rpm package dependence ,maintainer, patch query and so no.
License:        Mulan 2.0
URL:            https://gitee.com/openeuler/openEuler-Advisor
Source0:        https://gitee.com/openeuler/openEuler-Advisor/pkgship-%{version}.tar.gz

BuildArch:      noarch

Requires: python3-pip python3-flask-restful python3-flask python3 python3-pyyaml
Requires: python3-sqlalchemy python3-prettytable python3-requests
#Requires: pyinstaller python3-flask-session python3-flask-script marshmallow uwsig

%description
Pkgship implements rpm package dependence ,maintainer, patch query and so no.

%prep
%autosetup -n pkgship-%{version}

%build
%py3_build

%install
%py3_install


%check
%{__python3} -m unittest test/run_tests.py

%post
#build cli bin
if [ -f "/usr/bin/pkgship" ]; then
    rm -rf /usr/bin/pkgship
fi


cd %{python3_sitelib}/packageship/
if [ -f "/usr/bin/pyinstaller" ]; then
    /usr/bin/pyinstaller -F pkgship.py
elif [ -f "/usr/local/bin/pyinstaller" ]; then
    /usr/local/bin/pyinstaller -F pkgship.py
else
    echo "pkship install fail,there is no pyinstaller!"
    exit
fi

sed -i "s/hiddenimports\=\[\]/hiddenimports\=\['pkg_resources.py2_warn'\]/g" pkgship.spec
/usr/local/bin/pyinstaller pkgship.spec
cp dist/pkgship /usr/bin/
rm -rf %{python3_sitelib}/packageship/build %{python3_sitelib}/packageship/dist

%postun


%files
%doc README.md 
%{python3_sitelib}/*
%config %{_sysconfdir}/pkgship/*
%attr(0755,root,root) %{_bindir}/pkgshipd


%changelog
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
