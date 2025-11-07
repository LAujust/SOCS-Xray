Fetch Data
===================

Download EP data
----------------------

Sometimes you need long term EP data or some level 1 or 2-3 data for identification. Here er provide a tool for retrieving these data. 

For FXT Data, you EP TDIC account and password are required.

.. code-block:: python

    SOCS_Xray.download_fxt_data(username="account",
         password="password",
         ra=75.3897,
         dec=-47.0878,
         start_time="2025-09-27 00:00:00",
         end_time="2025-10-01 00:00:00",
         destination_path="/path/to/your/workspace"
     )

For WXT Data, we retrieve from EP Data Server. Therefore, your account and password to access the server are required (and this is different from your TDIC Account!).

.. code-block:: python

    SOCS_Xray.download_wxt_data(
        username="usrname",
        password="password",
        ra=75.3897,
        dec=-47.0878,
        start_time="2025-09-27 00:00:00",
        end_time="2025-10-01 00:00:00",
        remote_path="/mnt/epdata_pipeline/L23/obs/11900076167/ep11900076167wxt24po_cl.evt ",
        local_path="/path/to/your/workspace"
    )
