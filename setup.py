import os
import sys
from setuptools import setup

this_dir = os.path.dirname(__file__)
long_description = "\n" + open(os.path.join(this_dir, 'README.rst')).read()

setup(
    name='pydockerize',
    version='0.0.0',
    description=('Creates a Docker image from a Python app'),
    long_description=long_description,
    keywords='Docker',
    author='Marc Abramowitz',
    author_email='marc@marc-abramowitz.com',
    url='https://github.com/msabramo/pydockerize',
    py_modules=['pydockerize'],
    zip_safe=False,
    install_requires=['click'],
    entry_points = """\
      [console_scripts]
      pydockerize = pydockerize:pydockerize
    """,
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Testing',
        'Natural Language :: English',
        'Intended Audience :: Developers',
    ],
)
