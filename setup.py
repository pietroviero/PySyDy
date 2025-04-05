from setuptools import setup, find_packages

setup(
    name='pysydy',  
    version='0.1.0',
    packages=find_packages(where='pysydy'), 
    package_dir={'': 'pysydy'}, 
    install_requires=[], 
    author='Pietro Viero', 
    author_email='pietro.viero1@gmail.com', 
    description='A simple System Dynamics library in Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/pietroviero/PySyDy.git', 
    license='MIT', 
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
