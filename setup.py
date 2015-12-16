#!/usr/bin/env python
from distutils.core import setup

from annotation_manager import __version__

setup(
    name='annotation_manager',
    version=__version__,
    description='Document annotation manager',
    long_description='''Document annotation manager and synchronizer.''',
    license='BSD',
    author='Martin Pecka',
    author_email='peci1 at seznam dot cz',
    url='',
    packages=[
        'annotation_manager',
    ],
    keywords=['pdfloc', 'pdf converter', 'annotation'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Topic :: Utilities',
    ],
    requires=['pdfminer', 'pdfloc_converter']
)
