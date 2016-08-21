from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.5.2'

install_requires = [
    'pylint'
]


setup(name='setuptools-lint',
      version=version,
      description="Setuptools command for pylint",
      long_description=README + '\n\n' + NEWS,
      classifiers=[
          "Topic :: Documentation",
          "Framework :: Setuptools Plugin",
          "Development Status :: 4 - Beta",
          "Programming Language :: Python",
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          'License :: OSI Approved :: BSD License',
          "Topic :: Software Development :: Documentation",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      keywords='pylint setuptools command',
      author='Xavier Barbosa',
      author_email='',
      url='https://github.com/johnnoone/setuptools-pylint',
      license='BSD',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      entry_points={
          "distutils.commands": [
              "lint = setuptools_lint.setuptools_command:PylintCommand",
          ],
          "distutils.setup_keywords": [
              "lint_rcfile = setuptools_lint.setuptools_command:validate_rcfile",  # NOQA
          ],
      }
)
