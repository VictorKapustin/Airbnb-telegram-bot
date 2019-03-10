Airbnbot
========
This bot is made to track new listings that matches with your filters.

Installing
----------
Download and extract files in directory.
Create virtual environment
Install required modules from "Requirements.txt":

.. code-block:: text

    pip install -r Requirements.txt

Parameters
----------
currency
adults
children
price_min
price_max
checkin
checkout
room_types

Description
-----------
This bot do not requires your login.

Settings
--------
Create file settings.py
.. code-block:: text

    key_bot = "YOUR KEY FROM @BotFather"
    PROXY = {'proxy_url': 'socks5://YOUR_URL_PROXY:1080','urllib3_proxy_kwargs': {'username': 'LOGIN', 'password': 'PASS'}}
