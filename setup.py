# -*- encoding: utf-8 -*-

from setuptools import setup, find_packages

setup(

    # Name of the package:
    name='deel-dataset',

    # Version of the package:
    version="0.0.3",

    # Find the package automatically (include everything):
    packages=find_packages(),

    # Author information:
    author="DEEL",
    author_email="collaborateurs.du.projet.deel@irt-saintexupery.com",

    # Description of the package:
    description="Dataset loader for DEEL datasets",
    long_description=open('README.md').read(),
    include_package_data=True,

    # URL for sources:
    url='https://forge.deel.ai/bertrand.cayssiols/deel_dataset_manager',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # License:
    license="WTFPL",

    # Requirements:
    install_requires=[
        'requests==2.22.0',
        'h5py'
    ]
)
