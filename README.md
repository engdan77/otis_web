edoWeb
==============


Background
--------------

This project meant to be used for various purpose, but currently acts a front-end to edoAutoHome (home-monitoring)
https://github.com/engdan77/edoautohome


----------------------
Installing the dependencies and edoAutoHome
----------------------

1) Follow instrunctions found on http://web2py.com/books/default/chapter/29/13/deployment-recipes to install Web2Py framework
2) Enter "application" folder and retrieve source from github
```
# git clone https://github.com/engdan77/edoWeb.git
```
3) Adjust the modules/edoConf.py to reflect your database and URL's
```
# vim modules/edoConf.py

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *

db_AH = 'mysql://user:pass@192.168.0.1/edoAutoHome'
mail_settings_sender = 'xxxx@gmail.com'
mail_settings_login = 'xxxx@gmail.com:yyyyyy'
edoweb_url = "http://xxxx/"
response_meta_author = 'Daniel Engvall <daniel@engvalls.eu>'
```

-------------------------
Pictures
-------------------------
*Example of current status of sensors*
![Sensors](https://github.com/engdan77/edoWeb/blob/master/pics/edoWeb_sensors.png)
