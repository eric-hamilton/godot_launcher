from setuptools import setup


with open('requirements.txt') as f:
    requirements = f.read().splitlines()
    
    
setup(
    name='godot_launcher',
    version='0.1.0',
    description='An unofficial launcher to manage and install different versions of Godot.',
    author='Eric Hamilton',
    packages=['godot_launcher'],
    install_requires=requirements,
)
