Name:             bluez
Summary:          Bluetooth utilities
Version:          5.50
Release:          9
License:          GPLv2+
URL:              http://www.bluez.org/
Source0:          http://www.kernel.org/pub/linux/bluetooth/bluez-%{version}.tar.xz
# The following sources all come from upstream
Source1:          bluez.gitignore
Source2:          69-btattach-bcm.rules
Source3:          btattach-bcm@.service
Source4:          btattach-bcm-service.sh

Patch0001:        0001-build-Enable-BIND_NOW.patch
Patch0003:        0001-obex-Use-GLib-helper-function-to-manipulate-paths.patch
Patch0004:        0001-build-Always-define-confdir-and-statedir.patch
Patch0005:        0002-systemd-Add-PrivateTmp-and-NoNewPrivileges-options.patch
Patch0006:        0003-systemd-Add-more-filesystem-lockdown.patch
Patch0007:        0004-systemd-More-lockdown.patch
Patch0008:        0001-policy-Add-logic-to-connect-a-Sink.patch
Patch0009:        fix-CVE-2018-10910-1.patch
Patch0010:        fix-CVE-2018-10910-2.patch

Patch0011:        CVE-2020-0556-1.patch
Patch0012:        CVE-2020-0556-2.patch
Patch0013:        CVE-2020-0556-3.patch
Patch0014:        CVE-2020-0556-4.patch

BuildRequires:    dbus-devel >= 1.6
BuildRequires:    git-core glib2-devel libical-devel readline-devel libell-devel
BuildRequires:    json-c-devel systemd-devel cups-devel libtool automake autoconf
Requires:         dbus >= 1.6 %{name}-libs = %{version}-%{release}
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
Provides:         bluez-hid2hci bluez-obexd
Obsoletes:        bluez-hid2hci bluez-obexd

%description
This package provides all utilities for use in Bluetooth applications.
The BLUETOOTH trademarks are owned by Bluetooth SIG, Inc., U.S.A.

%package          libs
Summary:          Libraries for bluez

%description      libs
Libraries forbluez.

%package          devel
Summary:          Development libraries for Bluetooth applications
Requires:         %{name}-libs = %{version}-%{release}
Provides:         bluez-libs-devel
Obsoletes:        bluez-libs-devel

%description      devel
This package provides development libraries and headers for Bluetooth related
applications.

%package          help
Summary: Help manual for bluetooth application related utilities

%description      help
This package provides help manual function for Bluetooth utilities separately.

%package          cups
Summary: CUPS printer backend for Bluetooth printers
Requires: bluez%{?_isa} = %{version}-%{release}
Requires: cups

%description      cups
This package contains the CUPS backend

%prep
%autosetup -S git

%build
libtoolize -f
autoreconf -f -i
%configure --enable-tools --enable-library --enable-deprecated \
           --enable-sixaxis --enable-cups --enable-nfc --enable-mesh \
           --with-systemdsystemunitdir=%{_unitdir} \
           --with-systemduserunitdir=%{_userunitdir}
%make_build V=1

%install
%make_install
install -m0755 attrib/gatttool $RPM_BUILD_ROOT%{_bindir}

# Remove autocrap and libtool related redundant items
find $RPM_BUILD_ROOT -name '*.la' -delete

# Remove the cups backend from libdir, and install it in new default CUPS binary directory
if test -d ${RPM_BUILD_ROOT}/usr/lib64/cups ; then
        install -D -m0755 ${RPM_BUILD_ROOT}/usr/lib64/cups/backend/bluetooth ${RPM_BUILD_ROOT}%_cups_serverbin/backend/bluetooth
        rm -rf ${RPM_BUILD_ROOT}%{_libdir}/cups
fi

rm -f ${RPM_BUILD_ROOT}/%{_udevrulesdir}/*.rules
install -D -p -m0644 tools/hid2hci.rules ${RPM_BUILD_ROOT}/%{_udevrulesdir}/97-hid2hci.rules
install -d -m0755 $RPM_BUILD_ROOT/%{_localstatedir}/lib/bluetooth
install -d $RPM_BUILD_ROOT/%{_libdir}/bluetooth/

# Copy bluetooth config file
install -D -p -m0644 src/main.conf ${RPM_BUILD_ROOT}/etc/bluetooth/main.conf
# Setup auto enable
sed -i 's/#\[Policy\]$/\[Policy\]/; s/#AutoEnable=false/AutoEnable=true/' ${RPM_BUILD_ROOT}/%{_sysconfdir}/bluetooth/main.conf

# Serial port connected Broadcom HCIs scripts
install -D -p -m0644 %{SOURCE2} ${RPM_BUILD_ROOT}/%{_udevrulesdir}/
install -D -p -m0644 %{SOURCE3} ${RPM_BUILD_ROOT}/%{_unitdir}/
install -D -p -m0755 %{SOURCE4} ${RPM_BUILD_ROOT}/%{_libexecdir}/bluetooth/

%preun
%systemd_preun bluetooth.service
%systemd_user_preun obex.service

%post
%systemd_post bluetooth.service
/sbin/udevadm trigger --subsystem-match=usb
%systemd_user_post obex.service

%postun
%systemd_postun_with_restart bluetooth.service

%ldconfig_scriptlets libs

%files
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc AUTHORS ChangeLog
%config %{_sysconfdir}/dbus-1/system.d/bluetooth.conf
%config %{_sysconfdir}/bluetooth/main.conf
%{_bindir}/*
%{_libexecdir}/bluetooth/bluetoothd
%{_libexecdir}/bluetooth/btattach-bcm-service.sh
# This is obexd relative file
%{_libexecdir}/bluetooth/obexd
%{_libdir}/bluetooth/
# This is hid2hci relative file
%{_exec_prefix}/lib/udev/hid2hci
%{_localstatedir}/lib/bluetooth
%{_datadir}/dbus-1/system-services/org.bluez.service
# This is obexd relative file
%{_datadir}/dbus-1/services/org.bluez.obex.service
%{_unitdir}/bluetooth.service
%{_unitdir}/btattach-bcm@.service
%{_udevrulesdir}/69-btattach-bcm.rules
# hid2hci relative files
%{_udevrulesdir}/97-hid2hci.rules
# obexd relative files
%{_userunitdir}/obex.service

%files            libs
%{_libdir}/libbluetooth.so.*

%files            help
%{_mandir}/man1/*
%{_mandir}/man8/*

%files            devel
%doc doc/*txt
%{_libdir}/libbluetooth.so
%{_includedir}/bluetooth
%{_libdir}/pkgconfig/bluez.pc

%files            cups
%_cups_serverbin/backend/bluetooth

%changelog
* Wed May 20 2020 songnannan <songnannan2@huawei.com> - 5.50-9
- delete the check temporarily

* Wed Apr 22 2020 openEuler Buildteam <buildteam@openeuler.org> - 5.50-8
- Type:cves
- ID:CVE-2020-0556
- SUG:NA
- DESC:fix CVE-2020-0556

* Wed Mar 18 2020 chenzhen <chenzhen44@huawei.com> - 5.50-7
- Type:cves
- ID:CVE-2018-10910
- SUG:NA
- DESC:fix CVE-2018-10910

* Mon Feb 17 2020 hexiujun <hexiujun1@huawei.com> - 5.50-6
- Type:enhancement
- ID:NA
- SUG:NA
- DESC:unpack libs subpackage

* Sat Jan 11 2020 openEuler Buildteam <buildteam@openeuler.org> - 5.50-5
- Type:enhancement
- ID:NA
- SUG:NA
- DESC: delete patches

* Tue Sep 17 2019 Alex Chao <zhaolei746@huawei.com> - 5.50-4
- Package init
