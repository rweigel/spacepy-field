from setuptools import setup, find_packages

install_requires = [
    "numpy",
    "pandas",
    "spacepy",
    "utilrsw[mpl,io] @ git+https://github.com/rweigel/utilrsw@main"
]

setup(
    name='spacepy_field',
    version='0.0.1',
    author='Bob Weigel',
    author_email='rweigel@gmu.edu',
    packages=find_packages(),
    description='Wrapper for SpacePy interface to IRBEM magnetic field models',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    include_package_data=True,
)
