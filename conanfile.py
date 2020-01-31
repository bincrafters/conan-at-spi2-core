from conans import ConanFile, Meson, tools
from conans.errors import ConanInvalidConfiguration
import os
import shutil


class LibnameConan(ConanFile):
    name = "at-spi2-core"
    description = "It provides a Service Provider Interface for the Assistive Technologies available on the GNOME platform and a library against which applications can be linked"
    topics = ("conan", "atk", "accessibility")
    url = "https://github.com/bincrafters/conan-at-spi2-core"
    homepage = "https://gitlab.gnome.org/GNOME/at-spi2-core/"
    license = "LGPL-2.1"
    generators = "pkg_config"

    # Options may need to change depending on the packaged library
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_x11": [True, False],
        }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_x11": False,
        }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
    
    def build_requirements(self):
        self.build_requires('meson/0.53.0')
        if not tools.which('pkg-config'):
            self.build_requires('pkg-config_installer/0.29.2@bincrafters/stable')
    
    def requirements(self):
        self.requires('glib/2.58.3@bincrafters/stable')
        if self.options.with_x11:
            self.requires('libx11/1.6.8@bincrafters/stable')
            self.requires('libxtst/1.2.3@bincrafters/stable')
            self.requires('libxcb/1.13.1@bincrafters/stable')

    def system_requirements(self):
        if self.settings.os == 'Linux':
            installer = tools.SystemPackageTool()
            installer.install("libdbus-1-dev")

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_meson(self):
        meson = Meson(self)
        defs = {}
        defs['introspection'] = 'no'
        defs['docs'] = 'false'
        defs['x11'] = 'yes' if self.options.with_x11 else 'no'
        args=[]
        args.append('--wrap-mode=nofallback')
        meson.configure(defs=defs, build_folder=self._build_subfolder, source_folder=self._source_subfolder, pkg_config_paths='.', args=args)
        return meson

    def build(self):
        for package in self.deps_cpp_info.deps:
            lib_path = self.deps_cpp_info[package].rootpath
            for dirpath, _, filenames in os.walk(lib_path):
                for filename in filenames:
                    if filename.endswith('.pc'):
                        shutil.copyfile(os.path.join(dirpath, filename), filename)
                        tools.replace_prefix_in_pc_file(filename, lib_path)
        meson = self._configure_meson()
        meson.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        meson = self._configure_meson()
        meson.install()
        # If the CMakeLists.txt has a proper install method, the steps below may be redundant
        # If so, you can just remove the lines below
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = ['include/at-spi-2.0']
        
        def remove_prefix(s, prefix):
            return s[len(prefix):] if s.startswith(prefix) else s
        pkg = tools.PkgConfig("dbus-1")
        self.cpp_info.includedirs.extend([remove_prefix(x,'-I') for x in pkg.cflags_only_I])
        self.cpp_info.names['pkg_config'] = 'atspi-2'