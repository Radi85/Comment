import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name='django-comments-dab',
    version='1.2.2',
    packages=find_packages(exclude=['docs', 'test*']),
    include_package_data=True,
    author=u'Radico',
    author_email='mus.radi85@gmail.com',
    maintainer='Radi Mustafa',
    maintainer_email='mus.radi85@gmail.com',
    url='https://github.com/radi85/Comment',
    project_urls={
        'Documentation': 'https://django-comment-dab.readthedocs.io/index.html',
        'Source Code': 'https://github.com/radi85/Comment',
    },
    license='MIT',
    description='Django Comment Framework app. It can be associated with any given model.',
    long_description=README,
    install_requires=[
        'Django>=2.1.2',
        'django-widget-tweaks>=1.4.2',
        'djangorestframework==3.8.2',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1',
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
