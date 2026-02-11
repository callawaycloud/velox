from setuptools import setup, find_packages

setup(
    name="velox",
    version="0.1.0",
    description="Fast, lightweight data utilities for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Velox Contributors",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "matplotlib>=3.5",
    ],
    extras_require={
        "pandas": ["pandas>=1.3"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
