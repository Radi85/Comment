# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='django-comments-dab',
    version='1.0.0',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author=u'Radico',
    author_email='mus.radi85@gmail.com',
    maintainer='Radi Mustafa',
    maintainer_email='mus.radi85@gmail.com',
    url='https://github.com/radi85/Comment',
    license='MIT',
    description='Dango Comment Framework app. It can be associated with any given model.',
    install_requires=[
        'Django>=2.0',
        'django-widget-tweaks>=1.4.2',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='comments comment development',
    zip_safe=False,
)
