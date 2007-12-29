#!/usr/bin/python

import sys
import xmlrpclib
import optparse

SERVER='http://paste.debian.net'

def createProxy():
    return xmlrpclib.ServerProxy(SERVER)

def actionAddPaste(opts, args):
    cmd = args.pop(0)

    server = createProxy()
    code = args
    if len(args) == 0:
        code = [ i.strip() for i in sys.stdin.readlines() ]
    code = '\n'.join(code)
    result = server.paste.addPaste(code, opts.name, opts.expire, opts.lang)
    print result

def actionDelPaste(opts, args):
    cmd = args.pop(0)
    digest = args.pop(0)

    server = createProxy()
    result = server.paste.deletePaste(digest)

def actionGetPaste(opts, args):
    cmd = args.pop(0)
    id = args.pop(0)

    server = createProxy()
    result = server.paste.getPaste(id)
    print result

def actionGetLangs(opts, args):
    cmd = args.pop(0)

    server = createProxy()
    result = server.paste.getLanguages()
    print result


##
# MAIN
##
if __name__ == "__main__":
    actions = {'add'     : actionAddPaste,
               'del'     : actionDelPaste,
               'rm'      : actionDelPaste,
               'get'     : actionGetPaste,
               'getlangs': actionGetLangs,
               'langs'   : actionGetLangs }
    parser = optparse.OptionParser(usage="usage: %prog [options] ACTION <args>")
    parser.add_option('-n', '--name', default='anonymous', help="Name of poster")
    parser.add_option('-e', '--expire', type=int, default=72, metavar='HOURS',
            help='Time at wich the paste should expire')
    parser.add_option('-l', '--lang', default='plain', help='Type of highlighting')
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('Please provide me with an action')
    elif args[0] in actions:
        actions[args[0]](opts, args)
    else:
        parser.error('Unknown action: %s' % args[0])
