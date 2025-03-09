from setuptools import setup, find_packages

setup(
    name='pysydy',  # Package name (lowercase, usually same as directory)
    version='0.1.0',
    packages=find_packages(where='pysydy'), # find packages inside 'pysydy' directory
    package_dir={'': 'pysydy'}, # tell setuptools packages are under 'pysydy'
    install_requires=[], # List dependencies if any
    author='Pietro Viero', # Replace with your name
    author_email='pietro.viero1@gmail.com', # Replace with your email
    description='A simple System Dynamics library in Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/pietroviero/PySyDy.git', # Replace with your GitHub repo URL if you have one
    license='MIT', # Or your chosen license
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)