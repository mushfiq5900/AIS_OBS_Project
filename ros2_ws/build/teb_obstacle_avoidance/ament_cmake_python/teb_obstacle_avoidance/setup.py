from setuptools import find_packages
from setuptools import setup

setup(
    name='teb_obstacle_avoidance',
    version='0.1.0',
    packages=find_packages(
        include=('teb_obstacle_avoidance', 'teb_obstacle_avoidance.*')),
)
