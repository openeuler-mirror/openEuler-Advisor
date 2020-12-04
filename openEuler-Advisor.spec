Name:       openEuler-Advisor
Version:    1.0
Release:    3
Summary:    Collection of automatic tools for easily maintaining openEuler 
Group:	    Application
License:    Mulan PSL v2
URL:	    https://gitee.com/openeuler/openEuler-Advisor
Source0:    https://gitee.com/openeuler/openEuler-Advisor/%{name}-%{version}.tar.gz
BuildArch:  noarch
BuildRequires: python3 pytest
Requires:   python3-pyrpm python3-pyyaml python36-requests rpmdevtools python-BeautifulSoup yum-utils

%description
Collection of automatic tools for easily maintaining openEuler

%prep
%autosetup -n %{name}-%{version} -p1

%build
%py3_build

%install
%py3_install

%check
py.test-%{python3_version} -vv tests || :

%post

%postun

%files
%doc README.* AUTHORS RELEASES.md
%license LICENSE 
%{python3_sitelib}/*
%attr(0755,root,root) %{_bindir}/simple_update_robot
%attr(0755,root,root) %{_bindir}/oa_upgradable
%attr(0755,root,root) %{_bindir}/check_missing_file
%attr(0755,root,root) %{_bindir}/check_repeated_repo
%attr(0755,root,root) %{_bindir}/check_source_url
%attr(0755,root,root) %{_bindir}/create_repo
%attr(0755,root,root) %{_bindir}/create_repo_with_srpm
%attr(0755,root,root) %{_bindir}/psrtool
%attr(0755,root,root) %{_bindir}/review_tool
%attr(0755,root,root) %{_bindir}/tc_reminder
%attr(0755,root,root) %{_bindir}/which_archived
%attr(0755,root,root) %{_bindir}/prow_review_tool.py

%changelog
* Tue Dec 1 2020 smileknife <jackshan2010@aliyun.com> - 1.0-3
- review_tool: support for ci/cd framework prow

* Tue Dec 1 2020 smileknife <jackshan2010@aliyun.com> - 1.0-2
- Optimize editing mode for review items

* Sat Oct 17 2020 Leo Fang <leofang_94@163.com> - 1.0-1
- Package init
