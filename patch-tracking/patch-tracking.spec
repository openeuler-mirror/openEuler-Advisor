%define name patch-tracking
%define version 1.0.0
%define release 1

Summary: This is a tool for automatically tracking upstream repository code patches
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar
License: Mulan PSL v2
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: ChenYanpan <chenyanpan@huawei.com>
Url: https://openeuler.org/zh/

BuildRequires: python3-setuptools
# Requires: python3.7 python3-flask python3-sqlalchemy python3-requests

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
