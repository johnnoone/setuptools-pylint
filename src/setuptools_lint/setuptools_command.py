import re
import sys
import setuptools
from pylint import lint

_opts = lint.Run.LinterClass.make_options()

def user_options():
    parsed = []

    for longopt, params in _opts:
        shortopt = params.get('short', None)
        desc = params.get('help', None)

        parsed.append((longopt+'=', shortopt, desc))
    return parsed

class PylintCommand(setuptools.Command):
    description = "run pylint on all your modules"
    user_options = user_options() + [
        ('exclude-packages=', None, 'exclude packages?'),
        ('file=', None, "write into this file"),
    ]

    def initialize_options(self):
        self.exclude_packages = 'tests test'
        self.file = None
        for longopt, params in _opts:
            setattr(self, longopt.replace('-', '_'), None)

    def finalize_options(self):
        self.exclude_packages = [module.strip() \
            for module in re.split('[\s,]+', self.exclude_packages)]
        if self.file:
            self.file = open(self.file, 'w')

    def run(self):
        options = []
        for longopt, params in _opts:
            value = getattr(self, longopt.replace('-', '_'))
            if value is not None:
                if ' ' in value:
                    value = '"' + value + '"'
                options.append('--{0}={1}'.format(longopt, value))

        files = []
        base = self.get_finalized_command('build_py')
        for (package, module, filename) in base.find_all_modules():
            if package in self.exclude_packages:
                continue
            files.append(filename)

        if self.file:
            stdout, sys.stdout = sys.stdout, self.file
        lint.Run(options + files)
        if self.file:
            sys.stdout = stdout
