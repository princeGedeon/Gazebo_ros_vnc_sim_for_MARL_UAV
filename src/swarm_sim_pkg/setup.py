
from setuptools import setup
import os
from glob import glob

package_name = 'swarm_sim'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name, 'swarm_sim.common', 'swarm_sim.envs', 'swarm_sim.envs.core', 'swarm_sim.envs.single_agent', 'swarm_sim.envs.multi_agent', 'swarm_sim.training'],
    package_dir={'': '.'}, 
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name, ['default.rviz']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ] + [
        (os.path.join('share', package_name, os.path.dirname(p).replace('swarm_sim/', '', 1)), [p]) 
        for p in glob('swarm_sim/assets/**/*', recursive=True) if os.path.isfile(p) and '.git' not in p
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='User',
    maintainer_email='user@example.com',
    description='Swarm Sim',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'train_single = swarm_sim.training.train_single:main',
            'train_swarm = swarm_sim.training.train_swarm:main',
        ],
    },
)
