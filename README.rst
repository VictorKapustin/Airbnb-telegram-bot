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

airbnb-python
-------------

This api library was slightly customized.
Copy and Replace these functions in api.py

.. code-block:: text

    def get_homes(self, query=None, gps_lat=None, gps_lng=None, offset=0, items_per_grid=50,
                  adults=1, children=0, price_min=10, price_max=1006,
                  checkin=datetime.date.today()+datetime.timedelta(days=1),
                  checkout=datetime.date.today()+datetime.timedelta(days=2),
                  room_types=[]):
        """
        Search listings with
            * Query (e.g. query="Lisbon, Portugal") or
            * Location (e.g. gps_lat=55.6123352&gps_lng=37.7117917)
        """
        params = {
            'is_guided_search': 'true',
            'version': '1.3.9',
            'section_offset': '0',
            'items_offset': str(offset),
            'adults': str(adults),
            'children': str(children),
            'price_min': str(price_min),
            'price_max': str(price_max),
            'checkin': str(checkin),
            'checkout': str(checkout),
            'room_types[]': room_types, # ['Entire home/apt', 'Private room', 'Shared room']
            'screen_size': 'small',
            'source': 'explore_tabs',
            'items_per_grid': str(items_per_grid),
            '_format': 'for_explore_search_native',
            'metadata_only': 'false',
            'refinement_paths[]': '/homes',
            'timezone': 'Europe/Lisbon',
            'satori_version': '1.0.7'
        }

.. code-block:: text

    def __init__(self, username=None, password=None, access_token=None, api_key=API_KEY, session_cookie=None,
                 proxy=None, randomize=None, currency='USD'):
        self._session = requests.Session()
        self._access_token = None
        self.user_agent = "Airbnb/19.02 AppVersion/19.02 iPhone/12.1.2 Type/Phone"
        self.udid = "9120210f8fb1ae837affff54a0a2f64da821d227"
        self.uuid = "C326397B-3A38-474B-973B-F022E6E4E6CC"
        self.randomize = randomize

        self._session.headers = {
            "accept": "application/json",
            "accept-encoding": "br, gzip, deflate",
            "content-type": "application/json",
            "x-airbnb-api-key": api_key,
            "user-agent": self.user_agent,
            "x-airbnb-screensize": "w=375.00;h=812.00",
            "x-airbnb-carrier-name": "T-Mobile",
            "x-airbnb-network-type": "wifi",
            "x-airbnb-currency": currency,    # Здесь меняется валюта
            "x-airbnb-locale": "en",
            "x-airbnb-carrier-country": "us",
            "accept-language": "en-us",
            "airbnb-device-id": self.udid,
            "x-airbnb-advertising-id": self.uuid
        }

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
This bot does not require your login.

Settings
--------
Create file settings.py

.. code-block:: text

    key_bot = "YOUR KEY FROM @BotFather"
    PROXY = {'proxy_url': 'socks5://YOUR_URL_PROXY:1080','urllib3_proxy_kwargs': {'username': 'LOGIN', 'password': 'PASS'}}
    SQLALCHEMY_DATABASE_URI = "PATH TO DATABASE FILE LOCATION"
