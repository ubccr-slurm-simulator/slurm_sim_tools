from setuptools import setup
from Cython.Build import cythonize

setup(
    name='slurmanalyser',
    description='tools for slurm simulator and slurm logs analysis',
    version='',
    packages=['slurmanalyser'],
    package_dir={"": "src"},
    ext_modules=cythonize("src/slurmanalyser/cyutils.pyx"),
    url='',
    license='',
    author='Nikolay Simakov',
    author_email='nikolays@buffalo.edu',
    zip_safe=False
)
