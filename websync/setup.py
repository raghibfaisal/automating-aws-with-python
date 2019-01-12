from setuptools import setup

setup(
    name='websync_1',
    version='0.1',
    author='Raghib Faisal',
    description='Websync is a tool that helps to deploy static websites to AWS',
    license='GPLv3+',
    packages=['websync_1'],
    url='https://github.com/raghibfaisal/automating-aws-with-python',
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        websync_1=websync_1.websync:cli
    '''


)
