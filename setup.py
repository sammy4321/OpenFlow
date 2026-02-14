from setuptools import setup, find_packages

setup(
    name='OpenFlow',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'mlx==0.11.1',
        'mlx-whisper==0.4.1',
        'faster-whisper==1.0.3',
        'sounddevice==0.4.6',
        'numpy==1.26.4',
        'pynput==1.7.6',
        'pyobjc==10.1',
        'pyobjc-framework-Cocoa==10.1',
        'pyobjc-framework-ApplicationServices==10.1',
        'pyobjc-framework-Quartz==10.1',
        'rumps==0.4.0',
        'rich==13.7.1',
        'watchdog==4.0.0',
        'requests==2.31.0',
    ],
    entry_points={
        'console_scripts': [
            'openflow=openflow.main:main',
        ],
    },
)
