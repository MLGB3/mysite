import os
from setuptools import setup

version = open(os.path.join("version.txt")).read().strip()

setup(
    name='mysite',
    version=version,
    packages=['mysite'],
    include_package_data=True,
    license='BSD License',
    description='A django product',
    long_description='Should have a readme file',
    url='http://www.example.com/',
    author='Your Name',
    author_email='yourname@example.com',
    classifiers=[
        'Framework :: Django',
    ],
)
