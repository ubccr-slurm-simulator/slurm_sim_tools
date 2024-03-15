from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    name='slurmanalyser',
    description='tools for slurm simulator and slurm logs analysis',
    version='',
    packages=['slurmanalyser'],
    package_dir={"": "src"},
    ext_modules=cythonize("src/slurmanalyser/cyutilization.pyx"),
    url='',
    license='',
    author='Nikolay Simakov',
    author_email='nikolays@buffalo.edu',
    zip_safe=False,
    include_dirs=[numpy.get_include()]
)

# Run dependency:
#    numpy, pandas, pymysql
# Run analysis:
#    pyarrow
# Build dependency:
#    cython?
# Test dependency:
#    pytest pytest-datadir pyarrow
