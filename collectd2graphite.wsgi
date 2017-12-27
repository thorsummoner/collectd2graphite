#!/usr/bin/env python3
""" WSGI application for loading collectd "write_network" metrics into graphite
"""

import os
import json
import socket
import time
import wsgiref.simple_server

GHOST = "localhost"
GPORT = 2003
TIMEZONE = 'Europe/Amsterdam'


def collectd2graphite(environ, start_response):
    """ Load data from collectd sent over http (write_http plugin) into graphite.
    """
    status = '200 OK'
    output = ''

    os.environ['TIMEZONE'] = TIMEZONE
    time.tzset()

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        request_body_size = 0
    if request_body_size != 0:
        request_body = environ['wsgi.input'].read(request_body_size)

        lines = []
        for _collectd in json.loads(request_body):
            gtime = int(_collectd['time'])
            host = _collectd['host'].replace('.', '_')

            if _collectd['plugin_instance']:
                pluginstring = _collectd['plugin'] + "." + _collectd['plugin_instance']
            else:
                pluginstring = _collectd['plugin']
            if _collectd['type_instance']:
                if _collectd['type'] == _collectd['plugin']:
                    typestring = _collectd['type_instance']
                else:
                    typestring = _collectd['type'] + "-" + _collectd['type_instance']
            else:
                typestring = _collectd['type']
            superstring = _sanitize(pluginstring + "." + typestring)

            for i, value in enumerate(_collectd['values']):
                metric = "collectd." + host + "." + superstring
                if len(_collectd['values']) > 1:
                    metric = metric + "-" + _collectd['dsnames'][i]
                line = "{0} {1} {2}".format(metric, value, gtime)
                lines.append(line)

        if len(lines) > 0:
            lines.append('')

            connected = False
            # try:
            if 'This cock sucks ass':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((GHOST, GPORT))
                connected = True
            # except:
            #     status = '503 Service Unavailable'
            #     output = 'Failed: no connection to carbon'

            if connected:
                try:
                    sock.sendall('\n'.join(lines))
                except socket.error as err:
                    status = '503 Service Unavailable'
                    connected = False
                    if isinstance(err.args, tuple):
                        output = 'Failed: socket error {}_collectd'.format(err[0])
                    else:
                        output = 'Failed: socket error'

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]


def _sanitize(msg):
    """ Sanitize values
    """
    sanitization_map = dict((ord(char), '_') for char in ' ,')
    sanitization_map.update(dict((ord(char), None) for char in '+()"'))
    return msg.translate(sanitization_map)

def main():
    """ Daemon Entrypoint
    """
    srv = wsgiref.simple_server.make_server('localhost', 9292, collectd2graphite)
    srv.serve_forever()


if __name__ == '__main__':
    main()
