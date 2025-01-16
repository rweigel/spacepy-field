from setuptools import setup, find_packages

install_requires = ["numpy", "spacepy"]

setup(
    name='spacepy_field',
    version='0.0.1',
    author='Bob Weigel',
    author_email='rweigel@gmu.edu',
    packages=find_packages(),
    description='Wrapper for SpacePy magnetic field models',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    include_package_data=True,
)
