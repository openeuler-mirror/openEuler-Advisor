Summary:    This is a tool for automatically tracking upstream repository code patches
Name:       patch-tracking
Version:    1.0.2
Release:    2
License:    Mulan PSL v2
URL:        https://gitee.com/openeuler/openEuler-Advisor
Source0:    patch-tracking-%{version}.tar
BuildArch:  noarch


BuildRequires: python3-setuptools
Requires: python3-uWSGI python3-flask python3-Flask-SQLAlchemy python3-Flask-APScheduler python3-Flask-HTTPAuth
Requires: python3-requests python3-pandas


%description
This is a tool for automatically tracking upstream repository code patches

%prep
%setup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%post
sed -i "s|\blogging.conf\b|/etc/patch-tracking/logging.conf|" %{python3_sitelib}/patch_tracking/app.py
sed -i "s|\bsqlite:///db.sqlite\b|sqlite:////var/patch-tracking/db.sqlite|" %{python3_sitelib}/patch_tracking/app.py
sed -i "s|\bsettings.conf\b|/etc/patch-tracking/settings.conf|" %{python3_sitelib}/patch_tracking/app.py
chmod +x /usr/bin/patch-tracking-cli
chmod +x /usr/bin/patch-tracking
chmod +x /usr/bin/generate_password
sed -i "s|\bpatch-tracking.log\b|/var/log/patch-tracking.log|" /etc/patch-tracking/logging.conf

%preun
%systemd_preun patch-tracking.service

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{python3_sitelib}/*
/etc/patch-tracking/logging.conf
/etc/patch-tracking/settings.conf
/usr/bin/patch-tracking
/usr/bin/patch-tracking-cli
/var/patch-tracking/db.sqlite
/usr/bin/generate_password
/usr/lib/systemd/system/patch-tracking.service


%changelog
* Sat Sep 12 2020 chenyanpan <chenyanpan@huawei.com> - 1.0.2-2
- Type: bugfix
- DESC: fixed name of python3-Flask-HTTPAuth

* Fri Sep 11 2020 chenyanpan <chenyanpan@huawei.com> - 1.0.2-1
- Type: bugfix
- DESC: fixed issues, specify Requires
- https://gitee.com/src-openeuler/patch-tracking/issues: I1TXTA I1TWVU I1TSG7 I1TYJV I1UAMC I1TYNW
- https://gitee.com/openeuler/docs/issues: I1U54H


* Mon Sep 07 2020 chenyanpan <chenyanpan@huawei.com> - 1.0.1-1
- Type: bugfix
- DESC: fixed issues related to the validity of service configuration items and command line parameters
