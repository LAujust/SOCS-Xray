# SOCS-Xray
Synthetic Optical Counterparts Searching for Time-domain X-ray Survey

By defult, the `pipeline` incorporates X-ray source candidates from EP-WXT and EP-FXT, with optical transient candidates from TNS, ZTF, LSST, .etc.

## Installation

- From source code

```
git clone git@github.com:LAujust/SOCS-Xray.git
```

- From `pip` (under construction)

```
pip install socs_xray
```

## Quick Start

If you have the account of EPSC, you can run the default pipeline in just few lines. 

```
import socs_xray

EMAIL = 'youremail'
PASSWORD = 'yourpass'

pipeline = socs_xray.Pipeline(email=EMAIL,password=PASSWORD)
pipeline.run()
```

## Default Pipeline

Here are the criteria for candidates evaluation,

- Gold: `dt < 1d` and is not AGN/Stellar;
- Silver: `dt < 1d` and is AGN/Stellar or `1d < dt < 7d` and is not AGN/Stellar;
- Bronze: otherwise.

Or we can have a ranking statistic, i.e. the probability of X-ray emission and Optical transients share the same origin:

$\mathcal{L} = (P_{\mathrm{X}} + P_{\mathrm{astro}})(1-P_{\mathrm{cc}})$

, where $P_{\mathrm{X}},P_{\mathrm{astro}}$ are the probability of 'real' source, and $P_{\mathrm{cc}}$ is the probability of chance coincidence, which can be estimated by simulation or statistics on data.