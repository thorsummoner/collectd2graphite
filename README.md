# collectd2graphite
Yet another Collectd to Graphite converter in Python


# Overview

Load data from collectd sent over http (write_http plugin) into graphite.

## Metrics format

  collect.hostname.metric...

Dots in hostnames will be replaced by `_`

## why not use write_graphite ?

We would if we could :)

Sometimes all you have is an HTTP connection..

## collectd config example

    LoadPlugin "write_http"

    <Plugin "write_http">
      <URL "http://collectd2graphite.endpoint:9292/collectd/post">
        Format "JSON"
      </URL>
    </Plugin>

## graphite storage-schemas.conf

    [collectd]
    pattern = ^collectd\..*
    priority = 100
    retentions = 10s:7d,1m:31d,10m:5y

