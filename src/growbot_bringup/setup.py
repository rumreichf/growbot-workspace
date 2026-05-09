from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'growbot_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]
	),

        ('share/' + package_name, ['package.xml']
	),
	(os.path.join('share', 'growbot_bringup', 'launch'),
		glob('growbot_bringup/launch/*.launch.py')
	),
	(
    	os.path.join('share', package_name, 'config'),
    		['config/nav2_params.yaml'],
	),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='frankie',
    maintainer_email='rumreichf@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
		'random_explorer = growbot_bringup.random_explorer:main'
        ],
    },
)
