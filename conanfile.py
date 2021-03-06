#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Conan receipt package for USB Library
"""
import os
from conans import ConanFile, AutoToolsBuildEnvironment, MSBuild, tools


class LibUSBConan(ConanFile):
    """Download libusb source, build and create package
    """
    name = "libusb"
    version = "1.0.22"
    settings = "os", "compiler", "build_type", "arch"
    topics = ("conan", "libusb", "usb", "device")
    options = {"shared": [True, False], "enableUdev": [True, False], "fPIC": [True, False]}
    default_options = {'shared': True, 'enableUdev': True, 'fPIC': True}
    homepage = "https://github.com/libusb/libusb"
    url = "http://github.com/jens-totemic/conan-libusb"
    license = "LGPL-2.1"
    description = "A cross-platform library to access USB devices"
    _source_subfolder = "source_subfolder"
    exports = ["LICENSE.md"]

    def source(self):
        release_name = "%s-%s" % (self.name, self.version)
        tools.get("{0}/releases/download/v{1}/{2}.tar.bz2".format(self.homepage, self.version, release_name),
                  sha256="75aeb9d59a4fdb800d329a545c2e6799f732362193b465ea198f2aa275518157")
        os.rename(release_name, self._source_subfolder)

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os != "Linux":
            del self.options.enableUdev
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC

    # def system_requirements(self):
    #     if self.settings.os == "Linux":
    #         if self.options.enableUdev:
    #             package_tool = tools.SystemPackageTool()
    #             libudev_name = ""
    #             os_info = tools.OSInfo()
    #             if os_info.with_apt:
    #                 libudev_name = "libudev-dev"
    #                 if tools.detected_architecture() == "x86_64" and str(self.settings.arch) == "x86":
    #                     libudev_name += ":i386"
    #                 elif "x86" in tools.detected_architecture():
    #                     if str(self.settings.arch) == "armhf":
    #                         libudev_name += ":armhf"
    #                     elif str(self.settings.arch) == "arm64":
    #                         libudev_name += ":arm64"
    #             elif os_info.with_yum:
    #                 libudev_name = "libudev-devel"
    #                 if tools.detected_architecture() == "x86_64" and str(self.settings.arch) == "x86":
    #                     libudev_name += ".i686"
    #             elif os_info.with_zypper:
    #                 libudev_name = "libudev-devel"
    #                 if tools.detected_architecture() == "x86_64" and str(self.settings.arch) == "x86":
    #                     libudev_name = "libudev-devel-32bit"
    #             elif os_info.with_pacman:
    #                 libudev_name = "libsystemd systemd"
    #             else:
    #                 self.output.warn("Could not install libudev: Undefined package name for current platform.")
    #                 return
    #             package_tool.install(packages=libudev_name, update=True)

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("libudev1/237@totemic/stable")

    def _build_visual_studio(self):
        with tools.chdir(self._source_subfolder):
            solution_file = "libusb_2015.sln"
            if self.settings.compiler.version == "12":
                solution_file = "libusb_2013.sln"
            elif self.settings.compiler.version == "11":
                solution_file = "libusb_2012.sln"
            solution_file = os.path.join("msvc", solution_file)
            platforms = {"x86":"Win32"}
            msbuild = MSBuild(self)
            msbuild.build(solution_file, platforms=platforms, upgrade_project=False)

    def _build_autotools(self, configure_args=None):
        env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        env_build.fpic = self.options.fPIC
        with tools.chdir(self._source_subfolder):
            env_build.configure(args=configure_args)
            env_build.make()
            env_build.make(args=["install"])

    def _build_mingw(self):
        configure_args = ['--enable-shared' if self.options.shared else '--disable-shared']
        configure_args.append('--enable-static' if not self.options.shared else '--disable-static')
        if self.settings.arch == "x86_64":
            configure_args.append('--host=x86_64-w64-mingw32')
        if self.settings.arch == "x86":
            configure_args.append('--build=i686-w64-mingw32')
            configure_args.append('--host=i686-w64-mingw32')
        self._build_autotools(configure_args)

    def _build_unix(self):
        configure_args = ['--enable-shared' if self.options.shared else '--disable-shared']
        configure_args.append('--enable-static' if not self.options.shared else '--disable-static')
        if self.settings.os == "Linux":
            configure_args.append('--enable-udev' if self.options.enableUdev else '--disable-udev')
        self._build_autotools(configure_args)

    def build(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self._build_visual_studio()
        elif self.settings.os == "Windows" and self.settings.compiler == "gcc":
            self._build_mingw()
        else:
            self._build_unix()

    def _package_visual_studio(self):
        self.copy(pattern="libusb.h", dst=os.path.join("include", "libusb-1.0"), src=os.path.join(self._source_subfolder, "libusb"), keep_path=False)
        arch = "x64" if self.settings.arch == "x86_64" else "Win32"
        source_dir = os.path.join(self._source_subfolder, arch, str(self.settings.build_type), "dll" if self.options.shared else "lib")
        if self.options.shared:
            self.copy(pattern="libusb-1.0.dll", dst="bin", src=source_dir, keep_path=False)
            self.copy(pattern="libusb-1.0.lib", dst="lib", src=source_dir, keep_path=False)
            self.copy(pattern="libusb-usbdk-1.0.dll", dst="bin", src=source_dir, keep_path=False)
            self.copy(pattern="libusb-usbdk-1.0.lib", dst="lib", src=source_dir, keep_path=False)
        else:
            self.copy(pattern="libusb-1.0.lib", dst="lib", src=source_dir, keep_path=False)
            self.copy(pattern="libusb-usbdk-1.0.lib", dst="lib", src=source_dir, keep_path=False)

    def package(self):
        self.copy("COPYING", src=self._source_subfolder, dst="licenses", keep_path=False)
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            self._package_visual_studio()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "libusb-1.0"))
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
            # if self.options.enableUdev:
            #     self.cpp_info.libs.append("udev")
        elif self.settings.os == "Macos":
            self.cpp_info.libs.append("objc")
            self.cpp_info.libs.append("-Wl,-framework,IOKit")
            self.cpp_info.libs.append("-Wl,-framework,CoreFoundation")
