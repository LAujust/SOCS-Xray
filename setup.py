from setuptools import setup, find_packages

setup(
    name="SOCS_Xray",                     # package name
    version="0.0.1",                      # initial version
    author="R. -D. Liang",
    author_email="liangrd@bao.ac.cn",
    description="A pipeline for searching optical counterparts for Einstein Probe.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/LAujust/SOCS-Xray",  # optional
    packages=find_packages(),              # automatically finds all packages
    install_requires=[
        "numpy",
        "matplotlib>=3.5",
        "pandas>2.2.3"
    ],
    python_requires=">=3.8",               # optional
)