#!/bin/sh
uwsgi_python3 --fastcgi-socket unix://.sock --wsgi-file collectd2graphite.wsgi --master --processes 2 --threads 2
