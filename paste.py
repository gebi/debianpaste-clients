#!/usr/bin/python

import sys
import xmlrpclib
import optparse

SERVER='http://localhost/paste.pl/server.pl'

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options] <code>")
    parser.add_option('-n', '--name', default='anonymous', help="Name of poster")
    (opts, args) = parser.parse_args()
    code = args
    if len(args) == 0:
        code = [ i.strip() for i in sys.stdin.readlines() ]
    code = '\n'.join(code)

    server = xmlrpclib.ServerProxy(SERVER)
    result = server.paste.addPaste(code, opts.name)
    print result.statusmessage
