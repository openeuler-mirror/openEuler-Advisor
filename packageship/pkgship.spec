Name:           pkgship
Version:        1.0
Release:        0
Summary:        Pkgship implements rpm package dependence ,maintainer, patch query and so no.
License:        Mulan 2.0
URL:            https://gitee.com/openeuler/openEuler-Advisor
Source0:        https://gitee.com/openeuler/openEuler-Advisor/pkgship-%{version}.tar

BuildArch:      noarch

Requires: python3-pip python3-flask-restful python3-flask python3.7 python3-pyyaml
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


%post
#build cli bin
if [ -f "/usr/bin/cli" ];then
    rm -rf /usr/bin/cli
fi


cd %{python3_sitelib}/packageship/
/usr/local/bin/pyinstaller -F cli.py
sed -i "s/hiddenimports\=\[\]/hiddenimports\=\['pkg_resources.py2_warn'\]/g" cli.spec
/usr/local/bin/pyinstaller cli.spec
cp dist/cli /usr/bin/
rm -rf %{python3_sitelib}/packageship/build %{python3_sitelib}/packageship/dist

%postun


%files
%doc README.md 
%{python3_sitelib}/*
%config %{_sysconfdir}/pkgship/*


%changelog
* Tue Jun 11 2020 Feng Hu <solar.hu@foxmail.com>
- add macro to build cli bin when rpm install

* Sat Jun 6 2020 Feng Hu  <solar.hu@foxmail.com>
- init package
