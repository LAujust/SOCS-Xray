Example Usage
=====================

This is an example code for use. 

Basic Pipeline
-------------------

All function for searching can be utilized by running ``Pipeline()``, and your account and password to access EP TDIC are required. 

.. code-block:: python

    import SOCS_Xray
    from astropy.table import Table
    from astropy.time import Time


    pipe = SOCS_Xray.Pipeline(email='account',
                              password='password',
                              root='/path/to/your/workspace')

    pipe.run()
    pipe.tns_match.pprint()
    pipe.ztf_match.pprint()

The ``Pipeline()`` will store result in ``matched.csv``, and it will check whether this file is exsist. If so, it will use it as previous matched candidates. Otherwise, it will create a empty one. 

