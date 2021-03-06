import setuptools

import legislice

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="legislice",
    version=legislice.__version__,
    author="Matt Carey",
    author_email="matt@authorityspoke.com",
    description="API client for fetching and comparing passages from legislation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mscarey/legislice",
    packages=setuptools.find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*", "old"]
    ),
    install_requires=[
        "anchorpoint",
        "apispec",
        "marshmallow",
        "python-dotenv",
        "requests",
        "roman",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Industry",
        "License :: Free To Use But Restricted",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: Sociology :: History",
    ],
    python_requires=">=3.7",
    include_package_data=True,
)
