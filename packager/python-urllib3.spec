Name:		python-urllib3
Version:	1.25.9
Release:	1
Summary:	HTTP library with thread-safe connection pooling, file post, and more.
License:	MIT
URL:		https://urllib3.readthedocs.io/
Source0:	https://files.pythonhosted.org/packages/05/8c/40cd6949373e23081b3ea20d5594ae523e681b6f472e600fbc95ed046a36/urllib3-1.25.9.tar.gz
BuildArch:	noarch

Requires:	python3-brotlipy >= 0.6.0
Requires:	python3-certifi
Requires:	python3-cryptography >= 1.3.4
Requires:	python3-idna >= 2.0.0
Requires:	python3-pyOpenSSL >= 0.14
Requires:	python3-ipaddress
Requires:	python3-PySocks != 1.5.7, python3-PySocks < 2.0, python3-PySocks >= 1.5.6

%description
urllib3 is a powerful, *sanity-friendly* HTTP client for Python. Much of the
Python ecosystem already uses urllib3 and you should too.
urllib3 brings many critical features that are missing from the Python
standard libraries:
- Thread safety.
- Connection pooling.
- Client-side SSL/TLS verification.
- File uploads with multipart encoding.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, and brotli encoding.
- Proxy support for HTTP and SOCKS.
- 100% test coverage.
urllib3 is powerful and easy to use::
    >>> import urllib3
    >>> http = urllib3.PoolManager()
    >>> r = http.request('GET', 'http://httpbin.org/robots.txt')
    >>> r.status
    200
    >>> r.data
    'User-agent: *\nDisallow: /deny\n'

%package -n python3-urllib3
Summary:	HTTP library with thread-safe connection pooling, file post, and more.
Provides:	python-urllib3
BuildRequires:	python3-devel
BuildRequires:	python3-setuptools
%description -n python3-urllib3
urllib3 is a powerful, *sanity-friendly* HTTP client for Python. Much of the
Python ecosystem already uses urllib3 and you should too.
urllib3 brings many critical features that are missing from the Python
standard libraries:
- Thread safety.
- Connection pooling.
- Client-side SSL/TLS verification.
- File uploads with multipart encoding.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, and brotli encoding.
- Proxy support for HTTP and SOCKS.
- 100% test coverage.
urllib3 is powerful and easy to use::
    >>> import urllib3
    >>> http = urllib3.PoolManager()
    >>> r = http.request('GET', 'http://httpbin.org/robots.txt')
    >>> r.status
    200
    >>> r.data
    'User-agent: *\nDisallow: /deny\n'

%package help
Summary:	Development documents and examples for urllib3
Provides:	python3-urllib3-doc
%description help
urllib3 is a powerful, *sanity-friendly* HTTP client for Python. Much of the
Python ecosystem already uses urllib3 and you should too.
urllib3 brings many critical features that are missing from the Python
standard libraries:
- Thread safety.
- Connection pooling.
- Client-side SSL/TLS verification.
- File uploads with multipart encoding.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, and brotli encoding.
- Proxy support for HTTP and SOCKS.
- 100% test coverage.
urllib3 is powerful and easy to use::
    >>> import urllib3
    >>> http = urllib3.PoolManager()
    >>> r = http.request('GET', 'http://httpbin.org/robots.txt')
    >>> r.status
    200
    >>> r.data
    'User-agent: *\nDisallow: /deny\n'

%prep
%autosetup -n urllib3-1.25.9

%build
%py3_build

%install
%py3_install
install -d -m755 %{buildroot}/%{_pkgdocdir}
if [ -d doc ]; then cp -arf doc %{buildroot}/%{_pkgdocdir}; fi
if [ -d docs ]; then cp -arf docs %{buildroot}/%{_pkgdocdir}; fi
if [ -d example ]; then cp -arf example %{buildroot}/%{_pkgdocdir}; fi
if [ -d examples ]; then cp -arf examples %{buildroot}/%{_pkgdocdir}; fi
pushd %{buildroot}
if [ -d usr/lib ]; then
	find usr/lib -type f -printf "/%h/%f\n" >> filelist.lst
fi
if [ -d usr/lib64 ]; then
	find usr/lib64 -type f -printf "/%h/%f\n" >> filelist.lst
fi
if [ -d usr/bin ]; then
	find usr/bin -type f -printf "/%h/%f\n" >> filelist.lst
fi
if [ -d usr/sbin ]; then
	find usr/sbin -type f -printf "/%h/%f\n" >> filelist.lst
fi
popd
mv %{buildroot}/filelist.lst .

%files -n python3-urllib3 -f filelist.lst
%dir %{python3_sitelib}/*

%files help
%{_pkgdocdir}

%changelog
* Wed May 20 2020 Python_Bot <Python_Bot@openeuler.org>
- Package Spec generated
