# SOCS-Xray
Synthetic Optical Counterparts Searching for Time-domain X-ray Survey

By defult, the `pipeline` incorperates X-ray source candidates from EP-WXT and EP-FXT, with optical transient candidates from TNS, ZTF, LSST, .etc.

## Installization

- From source code

```
git clone git@github.com:LAujust/SOCS-Xray.git
```

- From `pip` (under construction)

```
pip install socs_xray
```

## Quick Start

If you have the account of EPSC , you can run the default pipeline in just few lines. 

```
import socs_xray

EMAIL = 'youremail'
PASSWORD = 'yourpass'

pipeline = socs_xray.Pipeline(email=EMAIL,password=PASSWORD)
pipeline.run()
```

