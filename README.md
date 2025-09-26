# SOCS-Xray
Synthetic Optical Counterparts Searching for Time-domain X-ray Survey

[![Hits-of-Code](https://hitsofcode.com/github/LAujust/SOCS-Xray?branch=master)](https://hitsofcode.com/github/LAujust/SOCS-Xray/view?branch=master)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

By defult, the `pipeline` incorporates X-ray source candidates from EP-WXT and EP-FXT, with optical transient candidates from TNS, ZTF, LSST, .etc. See details in the documentation [here](https://socs-xray.readthedocs.io/en/latest/).

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

The pipeline will create a folder at `./main`, where all output stored. 

Here are the criteria for candidates evaluation,

- Gold: `dt < 1d` and is not AGN/Stellar;
- Silver: `dt < 1d` and is AGN/Stellar or `1d < dt < 7d` and is not AGN/Stellar;
- Bronze: otherwise.

Or we can have a ranking statistic, i.e. the probability of X-ray emission and Optical transients share the same origin:

$\mathcal{L} = (P_{\mathrm{X}} + P_{\mathrm{astro}})(1-P_{\mathrm{cc}})$

, where $P_{\mathrm{X}},P_{\mathrm{astro}}$ are the probability of 'real' source, and $P_{\mathrm{cc}}$ is the probability of chance coincidence, which can be estimated by simulation or statistics on data.


All matched candidates satisfied designed filter will be stored in `./main/matched.csv`, with unique `ID`(`EP_name`) as tuple of X-ray/Optical name pair, i.e. (EP240506a, AT2024ofs), (A85_1, SN025ujd). Note: The FXT name in the pair is designated as the `target_name + i`, where `i` represent this is the $i$ th matched transient to the target. 

You can run this pipeline daily or hourly, by just modifying the example code `daily_update.py`, in which you should set all account and password, and email config (which use SSH priorly), and use [`cron`](https://en.wikipedia.org/wiki/Cron) to run at certain time. Alternatively, it also can be run in the workflow [Daily Run] (fork repo needed), in which you should set all account/password in `Settings -> Secrets and Variables -> Actions -> New repository secret`. Required Keys are list below:

| Secret Name   | Description | Example |
|--------|-----|-------|
| TDIC_EMAIL  | EP Account  | usrname    |
| TDIC_PASSWORD    | EP Password  | password    |
| SMTP_SERVER| SMTP server  | mail.ustc.edu.cn    |
| SMTP_PORT  | SMTP Port (465 for SSH)  | 465    |
| SENDER_EMAIL  | sender email  | youremail@mail.ustc.edu.cn |
| SENDER_PASSWORD  | sender password (which is different from login password)  | pass |

The receiver mail list should be written in a `mail_list.txt` file. 