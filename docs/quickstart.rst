Quick Start
=======================

This is a quick guidance for using the SOCS_Xray to systematically search Optical Counterparts. 


Installation
-----------------------

- From Source

.. code-block:: bash

    git clone https://github.com/LAujust/SOCS-Xray.git

    cd SOCS-Xray/

    pip install .

- From pip (under assessment)

.. code-block:: bash

    pip install socs_xray



Configuration of Accounts
---------------------------

Einstein Probe
============================

Before you start, you should have EP accounts registered. 


Email
============================

If you want to have email notification, you should setup smtp server by calling `send_email`. 


Run the pipeline
---------------------------

.. code-block:: python

    import SOCS_Xray

    tdic_email = 'your email'
    tdic_password = 'password'
    dt = [-10,30]  #time constraint between (-10,30) days

    pipe = SOCS_Xray.Pipeline(email=tdic_email,
                          password=tdic_password,
                          root='./',) 

    pipe.run(dt=dt,update_result=True,show_progress=True)


The default results will be stored at `matched.csv`, and if a pre-exsisting file is detected, new result will appened if `update_result=True`. 


Email Notification
--------------------------

We provide wrapped email sending module using `SMTP`. You can also define null notice when no sources matched for this run. 

.. code-block:: python

    smtp_server = 'server'
    smtp_port = 465
    sender_email = 'sender'
    sender_password = 'password'

    null_notice = """
                    <html>
                    <body>
                    <p>No matched candidates at %s. 
                    <p>Matched with %s TNS sources, %s ZTF sources and %s LSST sources. 
                                            <p>Running time: %.2f seconds. 
                    <p>Best regards,<br>Runduo</p>
                    </body>
                    </html>
                    """%(Time.now(),len(pipe.TNS_table),len(pipe.ZTF_clean), len(pipe.LSST_clean),pipe.elapsed_time)

    SOCS_Xray.send_email(smtp_server=smtp_server,
                            sender_email=sender_email,
                            smtp_port=smtp_port,
                            receiver_emails=receiver_emails,
                            password=sender_password,
                            html_body=null_notice)

