import os, sys, json, socket, time
from string import maketrans

ghost = "localhost"
gport = 2003
tz = 'Europe/Amsterdam'

def application(environ, start_response):
    global ghost, gport, tz

    status = '200 OK'
    output = 'Thanks'

    os.environ['TZ'] = tz
    time.tzset()

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
    except ValueError:
        request_body_size = 0
    if request_body_size != 0:
        request_body= environ['wsgi.input'].read(request_body_size)
        data = json.loads(request_body)

        lines = []
        for d in data:
            gtime = int(d['time'])
            host = d['host'].replace('.','_')
           
            if d['plugin_instance']:
                pluginstring = d['plugin'] + "." + d['plugin_instance']
            else:
                pluginstring = d['plugin']
            if d['type_instance']:
                if d['type'] == d['plugin']:
                    typestring = d['type_instance']
		else:
                    typestring = d['type'] + "-" + d['type_instance']
            else:
                typestring = d['type']
            superstring = graphiteFriendly(pluginstring + "." + typestring)

            for i, value in enumerate(d['values']):
                metric = "collectd." + host + "." + superstring
                if len(d['values']) > 1:
                    metric = metric + "-" + d['dsnames'][i]
                line = "{0} {1} {2}".format(metric, value, gtime)
                lines.append(line)

	if len(lines) > 0:
            lines.append('')

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ghost, gport))
                connected = True
            except:
                connected = False
                status = '503 Service Unavailable'
                output = 'Failed: no connection to carbon'

            if connected:
                try:
                    sock.sendall('\n'.join(lines))
                except socket.error, e:
                    status = '503 Service Unavailable'
                    connected = False
                    if isinstance(e.args, tuple):
                        output = 'Failed: socket error %d' % e[0]
                    else:
                        output = 'Failed: socket error'

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]

def graphiteFriendly(s):
    t = dict((ord(char), u'_') for char in ' ,')
    t.update(dict((ord(char), None) for char in '+()"'))
    return s.translate(t)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 9292, application)
    srv.serve_forever()
