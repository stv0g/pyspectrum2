#!/usr/bin/env python

import os
import codecs
from setuptools import setup

def read_file(filename, encoding='utf8'):
    """Read unicode from given file."""
    with codecs.open(filename, encoding=encoding) as fd:
        return fd.read()

here = os.path.abspath(os.path.dirname(__file__))
readme = read_file(os.path.join(here, 'README.rst'))

setup(name='pyspectrum2',
    version='0.1.0',
    description='pyspectrum2 implements the Protobuf-based interface to Spectrum2 required for building Python-based Spectrum2 backends',
    long_description=readme,
    keywords='spectrum2 xmpp im gateway transport',
    url='https://github.com/SpectrumIM/spectrum2',
    author='Steffen Vogel',
    author_email='post@steffenvogel.de',
    python_requires='>=3.5',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Operating System :: POSIX',
        'Topic :: Communications :: Chat'
    ],
    license='GPL-3+',
    packages=[
        'Spectrum2'
    ],
    install_requires=[
        'protobuf',
    ]
)
