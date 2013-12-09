%define enable_bootlogd_service 0
%define _disable_ld_no_undefined 1

Summary:	Programs which control basic system processes
Name:		sysvinit
Version:	2.87
Release:	22
License:	GPLv2+
Group:		System/Configuration/Boot and Init
Source0:	https://alioth.debian.org/frs/download.php/3060/sysvinit-%{version}.tar.gz
Source1:	bootlogd
Source2:	stop-bootlogd
URL:		https://alioth.debian.org/projects/pkg-sysvinit/
Patch1:		sysvinit-2.78-man.patch
Patch4:		sysvinit-2.86-autofsck.patch
Patch5:		sysvinit-2.86-loginshell.patch
Patch8:		sysvinit-2.86-inittab.patch
Patch10:	sysvinit-2.87-pidof.patch
Patch13:	sysvinit-2.86-single.patch
Patch16:	sysvinit-2.86-quiet.patch
Patch23:	sysvinit-2.86-pidof-man.patch
Patch24:	sysvinit-2.87-sulogin.patch
Patch25:	sysvinit-2.87-wide.patch
Patch26:	sysvinit-2.87-ipv6.patch
# Add -m option to pidof to omit processes that match existing omitted pids (#632321)
Patch27:	sysvinit-2.87-omit.patch
Patch28:	sysvinit-2.87-crypt-lib.patch

# Mandriva patches
Patch100:	sysvinit-2.86-shutdown.patch
Patch104:	sysvinit-2.85-walltty.patch
Patch105:	sysvinit-disable-respawn-more-quickly.patch
# do not try to take over console tty for rc.sysinit, it conflicts with speedboot (Mdv bug #58488)
Patch106:	sysvinit-2.87-speedboot-ioctl.patch

# Debian patches
Patch200:	50_bootlogd_devsubdir.patch
Patch201:	54_bootlogd_findptyfail.patch
Patch202:	55_bootlogd_flush.patch
Patch203:	99_ftbfs_define_enoioctlcmd.patch
BuildRequires:	glibc-static-devel
Requires:	pam >= 0.66-5
Requires(post):	coreutils
Requires:	sysvinit-tools = %{version}-%{release}
Obsoletes:	SysVinit < 2.86-6mdv2008.1
Provides:	SysVinit = %{version}-%{release}
Conflicts:	util-linux =< 2.24

%description
The sysvinit package contains a group of processes that control
the very basic functions of your system. sysvinit includes the init
program, the first program started by the Linux kernel when the
system boots. Init then controls the startup, running, and shutdown
of all other programs.

%package tools
Summary:	Tools used for process and utmp management
Group:		System/Configuration/Boot and Init
Conflicts:	sysvinit < 2.87-2mdv

%description tools
The sysvinit-tools package contains various tools used for process
management.


%prep
%setup -q -n sysvinit-%{version}dsf
# We use a shell, not sulogin. Other random man fixes go here (such as #192804)
%patch1 -p1 -b .manpatch
# Unlink /.autofsck on shutdown -f
%patch4 -p1 -b .autofsck
# Invoke single-user shell as a login shell (#105653)
%patch5 -p1 -b .loginshell
# Adjust examples in inittab(5) to more accurately reflect RH/Fedora
# usage (#173572)
%patch8 -p1 -b .inittabdocs
# Fix various things in pidof - pidof /x/y matching /z/y, pidof -x
# for scripts, etc.
%patch10 -p1 -b .pidof
# Fix single user mode (#176348)
%patch13 -p1 -b .single
# Be less verbose when booted with 'quiet'
%patch16 -p1 -b .quiet
# Document some of the behavior of pidof. (#201317)
%patch23 -p1 -b .pidof
# get_default_context_with_level returns 0 on success (#568530)
%patch24 -p1 -b .sulogin
# Add wide output names with -w (#550333)
%patch25 -p1 -b .wide
# Change accepted ipv6 addresses (#573346)
%patch26 -p1 -b .ipv6
# Support -m option for pidof (#632321)
%patch27 -p1 -b .omit
%patch28 -p1 -b .crypt_lib~

%patch100 -p1 -b .shutdown
%patch104 -p1 -b .wall
%patch105 -p1 -b .disable-respawn-more-quickly
%patch106 -p1 -b .speedboot-ioctl

%patch200 -p1 -b .bootlogd_devsubdir
%patch201 -p1 -b .bootlogd_findptyfail
%patch202 -p1 -b .bootlogd_flush
%patch203 -p1 -b .define_enoioctlcmd

%build
%global optflags %{optflags} -Os
%make CFLAGS="%{optflags} -D_GNU_SOURCE" LDFLAGS="%{ldflags}" LCRYPT="-lcrypt" -C src

%install
for I in bin sbin usr/{bin,include} %{_mandir}/man{1,3,5,8} etc var/run dev; do
	mkdir -p %{buildroot}/$I
done

make -C src ROOT=%{buildroot} MANDIR=%{_mandir} STRIP=/bin/true \
	BIN_OWNER=`id -nu` BIN_GROUP=`id -ng` install

# If this already exists, just do nothing (the ||: part)
mknod --mode=0600 %{buildroot}/dev/initctl p ||:
ln -snf killall5 %{buildroot}/sbin/pidof

chmod 755 %{buildroot}/usr/bin/utmpdump

mkdir -p %{buildroot}%{_sysconfdir}/rc.d/init.d/
install -m755 %{SOURCE1} %{SOURCE2} %{buildroot}%{_sysconfdir}/rc.d/init.d/

%if !%enable_bootlogd_service
sed -i -e 's/chkconfig\: 2345/chkconfig: -/g' %{buildroot}%{_sysconfdir}/rc.d/init.d/bootlogd %{buildroot}%{_sysconfdir}/rc.d/init.d/stop-bootlogd
%endif

mkdir -p  %{buildroot}%{_sysconfdir}/sysconfig
cat << EOF > %{buildroot}%{_sysconfdir}/sysconfig/bootlogd
BOOTLOGD_ENABLED=no
EOF

# Remove unpackaged file(s)
rm -rf	%{buildroot}/usr/include

# (tpg) kill these in the name of systemd

rm %{buildroot}/sbin/bootlogd
rm %{buildroot}/sbin/halt
rm %{buildroot}/sbin/init
rm %{buildroot}/sbin/poweroff
rm %{buildroot}/sbin/last
rm %{buildroot}/sbin/mesg
rm %{buildroot}/sbin/reboot
rm %{buildroot}/sbin/runlevel
rm %{buildroot}/sbin/shutdown
rm %{buildroot}/sbin/telinit
rm %{buildroot}%{_sysconfdir}/rc.d/init.d/*bootlogd
rm %{buildroot}%{_sysconfdir}/sysconfig/bootlogd
rm %{buildroot}%{_mandir}/man5/*
rm %{buildroot}%{_mandir}/man8/halt*
rm %{buildroot}%{_mandir}/man8/init*
rm %{buildroot}%{_mandir}/man1/last.*
rm %{buildroot}%{_mandir}/man1/mesg.*
rm %{buildroot}%{_mandir}/man8/poweroff*
rm %{buildroot}%{_mandir}/man8/reboot*
rm %{buildroot}%{_mandir}/man8/runlevel*
rm %{buildroot}%{_mandir}/man8/shutdown*
rm %{buildroot}%{_mandir}/man8/telinit*
rm %{buildroot}%{_mandir}/man8/bootlogd*
rm %{buildroot}%{_mandir}/man1/mountpoint*
rm %{buildroot}%{_mandir}/man1/wall*

# Remove sulogin and utmpdump, they're part of util-linux these days
rm %{buildroot}/sbin/sulogin %{buildroot}%{_mandir}/man8/sulogin*
rm %{buildroot}%{_bindir}/utmpdump
# (tpg) in util-linux-2.23
rm %{buildroot}/bin/mountpoint
rm %{buildroot}%{_bindir}/wall


%files tools
%defattr(-,root,root)
%doc doc/Changelog COPYRIGHT
/bin/pidof
%{_bindir}/lastb
/sbin/pidof
/sbin/killall5
%{_mandir}/man1/*
%{_mandir}/man8/killall5*
%{_mandir}/man8/pidof*
