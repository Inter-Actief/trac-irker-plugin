from setuptools import setup

setup(
    name='IrkerNotifcationPlugin',
    version='0.2',
    description='Plugin to announce Trac changes via Irker',
    author='Kurocon',
    url='https://github.com/Southen/trac-irker-plugin',
    license='BSD',
    packages=['irker_notification'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    entry_points={
        'trac.plugins': 'irker_notification = irker_notification'
    }
)
