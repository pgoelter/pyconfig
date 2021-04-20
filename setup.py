import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyconfig",
    version="0.1",
    author="pgoelter",
    author_email="pgoelter@gmail.com",
    description="Python package to manage configuration with a globally available configuration object that follows \
    the singleton pattern.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pgoelter/pyconfig",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
