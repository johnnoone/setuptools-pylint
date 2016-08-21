import os
import re
import sys
import setuptools
from distutils.errors import DistutilsSetupError, DistutilsError
from pylint import lint
from pkg_resources import *

_opts = lint.Run.LinterClass.make_options()


def user_options():
    parsed = []

    for longopt, params in _opts:
        desc = params.get('help', None)

        parsed.append(('lint-' + longopt + '=', None, desc))
    return parsed


def validate_rcfile(dist, attr, value):
    if not os.path.exists(value):
        raise DistutilsSetupError(
            "Cannot find PyLint configuration file %s" % value)


class DistutilsPylintError(DistutilsError):
    pass


class PylintCommand(setuptools.Command):
    description = "run pylint on all your modules"
    user_options = user_options() + [
        ('lint-packages=', None,
         'Report on just these packages. These arguments are passed straight '
         'through to pylint as the module_or_package arguments. As such, they '
         'can be paths to files or packages'),
        ('lint-exclude-packages=', None, 'exclude these packages'),
        ('lint-output=', None, "output report into this file"),
        ('lint-rcfile=', None, "pylint configuration file"),
    ]

    def initialize_options(self):
        self.lint_packages = ''
        self.lint_exclude_packages = 'tests test'
        self.lint_output = None
        self.lint_rcfile = self.distribution.lint_rcfile
        for longopt, params in _opts:
            key = 'lint_' + longopt.replace('-', '_').rstrip('=')
            setattr(self, key, None)

    def finalize_options(self):
        self.lint_packages = [package.strip()
                              for package
                              in re.split('[\s,]+', self.lint_packages)
                              if package != '']
        self.lint_exclude_packages = [module.strip()
            for module in re.split('[\s,]+', self.lint_exclude_packages)]
        if self.lint_output:
            out_dir = os.path.dirname(self.lint_output)
            if out_dir:
                if sys.version_info >= (3, 2):
                    os.makedirs(out_dir, exist_ok=True)
                elif not os.path.exists(out_dir):
                    os.makedirs(out_dir)
            self.lint_output = open(self.lint_output, 'w')

    def with_project_on_sys_path(self, func, func_args, func_kwargs):
        if sys.version_info >= (3,) \
           and getattr(self.distribution, 'use_2to3', False):
            # If we run 2to3 we can not do this inplace:

            # Ensure metadata is up-to-date
            self.reinitialize_command('build_py', inplace=0)
            self.run_command('build_py')
            bpy_cmd = self.get_finalized_command("build_py")
            build_path = normalize_path(bpy_cmd.build_lib)

            # Build extensions
            self.reinitialize_command('egg_info', egg_base=build_path)
            self.run_command('egg_info')

            self.reinitialize_command('build_ext', inplace=0)
            self.run_command('build_ext')
        else:
            # Without 2to3 inplace works fine:
            self.run_command('egg_info')

            # Build extensions in-place
            self.reinitialize_command('build_ext', inplace=1)
            self.run_command('build_ext')

        ei_cmd = self.get_finalized_command("egg_info")

        old_path = sys.path[:]
        old_modules = sys.modules.copy()

        try:
            sys.path.insert(0, normalize_path(ei_cmd.egg_base))
            working_set.__init__()
            add_activation_listener(lambda dist: dist.activate())
            require('%s==%s' % (ei_cmd.egg_name, ei_cmd.egg_version))
            return func(*func_args, **func_kwargs)
        finally:
            sys.path[:] = old_path
            sys.modules.clear()
            sys.modules.update(old_modules)
            working_set.__init__()

    def run(self):
        options = []
        for longopt, params in _opts + (("rcfile", None),):
            value = getattr(self, 'lint_' + longopt.replace('-', '_'))
            if value is not None:
                if ' ' in value:
                    value = '"' + value + '"'
                options.append('--{0}={1}'.format(longopt, value))

        if self.distribution.install_requires:
            self.distribution.fetch_build_eggs(
                self.distribution.install_requires)

        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        if self.lint_packages:
            # The user explicitly specified the paths/packages to send to lint
            files = self.lint_packages
        else:
            # With no packages specified, find all of them and pass them
            # through the filter
            base = self.get_finalized_command('build_py')
            files = [filename
                     for (package, module, filename)
                     in base.find_all_modules()
                     if package not in self.lint_exclude_packages]

        if self.lint_output:
            stdout, sys.stdout = sys.stdout, self.lint_output
            stderr, sys.stdout = sys.stderr, self.lint_output
        try:
            lint_runner = self.with_project_on_sys_path(lint.Run,
                                                        [options + files],
                                                        {'exit': False})
            if lint_runner.linter.msg_status:
                raise DistutilsPylintError(
                    "lint error %s." % lint_runner.linter.msg_status)
        finally:
            if self.lint_output:
                sys.stdout = stdout
                sys.stderr = stderr
