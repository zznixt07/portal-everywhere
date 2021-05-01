from setuptools import setup

setup(name='bot telegram sender',
    version=0.1,
    description='Send message to telegram using bots',
    url='https://zznixt.me',
    author='zznixt',
    author_email='zznixt07@protonmail.com',
    license='MIT',
    packages=['telegram'],
    install_requires=[
        'requests',
        'requests_toolbelt',
    ],
    zip_safe=False
)