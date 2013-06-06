%define enable_bootlogd_service 0
%define _disable_ld_no_undefined 1

Summary:	Programs which control basic system processes
Name:		sysvinit
Version:	2.87
Release:	17
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

# Remove sulogin and utmpdump, they're part of util-linux these days
rm %buildroot/sbin/sulogin %buildroot%_mandir/man8/sulogin*
rm %buildroot%_bindir/utmpdump

%post
%_post_service bootlogd
%_post_service stop-bootlogd

[ ! -p /dev/initctl ] && rm -f /dev/initctl && mknod --mode=0600 /dev/initctl p || :
[ -e /var/run/initrunlvl ] && ln -s ../var/run/initrunlvl /etc/initrunlvl || :
[ -x /sbin/telinit -a -p /dev/initctl -a -f /proc/1/exe -a -d /proc/1/root ] && /sbin/telinit u || :
exit 0

%preun
%_preun_service bootlogd
%_preun_service stop-bootlogd

%files
%defattr(-,root,root)
%doc doc/Propaganda doc/Install
%doc doc/sysvinit-*.lsm contrib/start-stop-daemon.* 
/sbin/bootlogd
/sbin/halt
/sbin/init
/sbin/poweroff
/sbin/reboot
/sbin/runlevel
/sbin/shutdown
/sbin/telinit
%{_mandir}/man5/*
%{_mandir}/man8/halt*
%{_mandir}/man8/init*
%{_mandir}/man8/poweroff*
%{_mandir}/man8/reboot*
%{_mandir}/man8/runlevel*
%{_mandir}/man8/shutdown*
%{_mandir}/man8/telinit*
%{_mandir}/man8/bootlogd*
%ghost /dev/initctl

%{_sysconfdir}/rc.d/init.d/*bootlogd
%config(noreplace) %{_sysconfdir}/sysconfig/bootlogd

%files tools
%defattr(-,root,root)
%doc doc/Changelog COPYRIGHT
/bin/mountpoint
/bin/pidof
%{_bindir}/last
%{_bindir}/lastb
%{_bindir}/mesg
%attr(2555,root,tty)  /usr/bin/wall
/sbin/pidof
/sbin/killall5
%{_mandir}/man1/*
%{_mandir}/man8/killall5*
%{_mandir}/man8/pidof*


%changelog
* Sun Aug 26 2012 Tomasz Pawel Gajc <tpg@mandriva.org> 2.87-13
+ Revision: 815792
- reupload

* Fri Aug 24 2012 Paulo Andrade <pcpa@mandriva.com.br> 2.87-12
+ Revision: 815705
- Bump release and rebuild.

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - fix linking against libcrypt

  + Bernhard Rosenkraenzer <bero@bero.eu>
    - Remove sulogin and utmpdump, they're part of util-linux now

* Sun May 15 2011 Oden Eriksson <oeriksson@mandriva.com> 2.87-10
+ Revision: 674748
- fix build (ubuntu)
- mass rebuild

* Thu Jan 27 2011 Eugeni Dodonov <eugeni@mandriva.com> 2.87-9
+ Revision: 633185
- Rebuild
- Fix typo in service name.

* Sun Nov 28 2010 Andrey Borzenkov <arvidjaar@mandriva.org> 2.87-8mdv2011.0
+ Revision: 602209
- P27: actually add backported patch

* Sat Nov 27 2010 Andrey Borzenkov <arvidjaar@mandriva.org> 2.87-7mdv2011.0
+ Revision: 601936
- P27: add pidof -m option for new initscripts

* Wed May 05 2010 Frederic Crozat <fcrozat@mandriva.com> 2.87-6mdv2010.1
+ Revision: 542413
- Patch106: do not try to take over console tty for rc.sysinit, it conflicts with speedboot (Mdv bug #58488)

* Tue May 04 2010 Frederic Crozat <fcrozat@mandriva.com> 2.87-5mdv2010.1
+ Revision: 542055
- Patch200 (Debian): fix tty search with udev
- Patch201 (Debian): ensure findpty returns error correctly
- Patch202 (Debian): flush cache on disk if needed
- Add initscripts for bootlogd (not enabled by default)

* Thu Apr 29 2010 Frederic Crozat <fcrozat@mandriva.com> 2.87-4mdv2010.1
+ Revision: 540863
- Patch24 (Fedora): get_default_context_with_level returns 0 on success (Fedora bug #568530)
- Patch25 (Fedora): Add wide output names with -w (Fedora bug #550333)
- Patch26 (Fedora): Change accepted ipv6 addresses (Fedora bug #573346)
- do not strip package at build time, ensure debug package isn't empty (Fedora)

* Mon Mar 15 2010 Oden Eriksson <oeriksson@mandriva.com> 2.87-3mdv2010.1
+ Revision: 520249
- rebuilt for 2010.1

* Wed Sep 09 2009 Frederic Crozat <fcrozat@mandriva.com> 2.87-2mdv2010.0
+ Revision: 435821
- Move non init related utilities to tools subpackage (Fedora)

* Wed Aug 12 2009 Frederic Crozat <fcrozat@mandriva.com> 2.87-1mdv2010.0
+ Revision: 415602
- Release 2.87dsf
- Remove a lot of patches merged upstream and sync with fedora patches

* Thu Jan 29 2009 Frederic Crozat <fcrozat@mandriva.com> 2.86-11mdv2009.1
+ Revision: 335131
- Patch21 (Fedora): Don't abort if policy is already loaded
- Patch22 (Fedora):  Document some of the behavior of pidof. (Fedora bug #201317)
- Patch24 (Fedora): Don't pass around unchecked malloc (and avoid a leak) (Fedora bug #473485)

* Sun Jan 25 2009 Tomasz Pawel Gajc <tpg@mandriva.org> 2.86-10mdv2009.1
+ Revision: 333578
- compile with %%ldflags
- spec file clean

* Mon Dec 22 2008 Oden Eriksson <oeriksson@mandriva.com> 2.86-9mdv2009.1
+ Revision: 317611
- rediffed some fuzzy patches

* Wed Jul 23 2008 Olivier Blin <blino@mandriva.org> 2.86-8mdv2009.0
+ Revision: 242989
- add more killall5 features (from Debian):
  o never attempt to kill init
  o exit with a proper code
  o "-o" option support to omit pids (to be used by splashy)

* Wed Jun 18 2008 Thierry Vignaud <tv@mandriva.org> 2.86-7mdv2009.0
+ Revision: 225597
- rebuild

* Mon Jan 28 2008 Olivier Blin <blino@mandriva.org> 2.86-6mdv2008.1
+ Revision: 159196
- require coreutils for post script (#19143)
- obsoletes/provides SysVinit
- rename as sysvinit
- rename SysVinit as sysvinit
- update license tag to GPLv2+
- update URL
- sync with Fedora patches
- remove old cpp hack
- use Fedora's version of timeval/varargs patches
- use Fedora's version of autofsck/chroot patches
- restore BuildRoot

* Mon Dec 17 2007 Thierry Vignaud <tv@mandriva.org> 2.86-5mdv2008.1
+ Revision: 128170
- kill re-definition of %%buildroot on Pixel's request

  + Olivier Blin <blino@mandriva.org>
    - restore previous SysVinit package


* Sat Sep 15 2007 Tomasz Pawel Gajc <tpg@mandriva.org> 2.86-6mdv2008.0
+ Revision: 85860
- sync patches with fedora (104-113)
- spec file clean
- soec file clean
- rename to be closer with upstream

