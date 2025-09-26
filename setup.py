from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='socs_xray',
    version='1.12.1',
    description='A Systematically Optical Counterpart Searching pipeline for Einstein Probe. ',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/LAujust/SOCS-Xray',
    author='R. D. Liang',
    author_email='liangrd@bao.ac.cn',
    license='Apache-2.0 license',
    packages=['socs_xray'],
    package_dir={'socs_xray': 'socs_xray', },
    #package_data={'socs_xray': ['priors/*', 'tables/*', 'plot_styles/*']},
    install_requires=[
        "numpy",
        "setuptools",
        "pandas",
        "scipy",
        "selenium",
        "matplotlib",
        "astropy",
        "extinction",
        "requests",
        "lxml",
        "sphinx-rtd-theme",
        "sphinx-tabs",
        "regex",
        "sncosmo",
        "afterglowpy",
    ],
    # extras_require={
    #     'all': [
    #         "nestle",
    #         "sherpa",
    #         "george",
    #         "scikit-learn",
    #         "PyQt5",
    #         "lalsuite",
    #         "kilonova-heating-rate",
    #         "redback-surrogates",
    #         "tensorflow",
    #         "keras",
    #         "kilonovanet",
    #         "astroquery",
    #         "pyphot==1.6.0",
    #     ]
    # },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache-2.0 license",
        "Operating System :: OS Independent",
    ],
    zip_safe=False
)