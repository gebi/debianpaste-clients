#!/usr/bin/python2
# Filename:      paste
# Purpose:       XmlRpc interface client to paste.debian.net
# Author:        Michael Gebetsroither <michael@mgeb.org>
# License:       This file is licensed under the GPL v2+.
################################################################################

import sys
import xmlrpclib
import optparse
import inspect
import getpass

# program defaults
DEFAULT_SERVER='http://paste.debian.net/server.pl'

class ActionFailedException(Exception):
    '''Thrown if server returned an error'''
    def __init__(self, errormsg, ret):
        Exception.__init__(self, errormsg, ret)
    def what(self):
        '''Get errormessage'''
        return self.args[0]
    def dwhat(self):
        '''Get more verbose errormessage'''
        return self.args[1]


class Action(object):
    def __init__(self, args, opts):
        self.args_ = args
        self.opts_ = opts

    def _createProxy(self):
        return xmlrpclib.ServerProxy(self.opts_.server, verbose=False)

    def _callProxy(self, functor, server=None):
        '''Wrapper for xml-rpc calls to server which throws an
           ActionFailedException on error'''
        if server is None:
            server = self._createProxy()
        ret = functor(server)
        if ret['rc'] != 0:
            raise ActionFailedException(ret['statusmessage'], ret)
        return ret

    def call(self, method_name):
        '''External Interface to call the appropriate action'''
        return self.__getattribute__(method_name)()

    def actionAddPaste(self):
        '''Add paste to the server: <1.line> <2.line> ...

        default     Read paste from stdin.
        [text]      Every argument on the commandline will be interpreted as
                    a seperate line of paste.
        '''
        server = self._createProxy()
        o = self.opts_
        code = self.args_
        if len(self.args_) == 0:
            code = [ i.rstrip() for i in sys.stdin.readlines() ]
        code = '\n'.join(code)
        result = self._callProxy(lambda s: s.paste.addPaste(code, o.name, o.expire * 3600, o.lang, o.private),
                            server)
        return (result['statusmessage'], result)

    def actionDelPaste(self):
        '''Delete paste from server: <digest>

        <digest>    Digest of paste you want to remove.
        '''
        digest = self.args_.pop(0)
        result = self._callProxy(lambda s: s.paste.deletePaste(digest))
        return (result['statusmessage'], result)

    def actionGetPaste(self):
        '''Get paste from server: <id>

        <id>        Id of paste you want to receive.
        '''
        id = self.args_.pop(0)
        result = self._callProxy(lambda s: s.paste.getPaste(id))
        return (result['code'], result)

    def actionGetLangs(self):
        '''Get supported language highlighting types from server'''
        result = self._callProxy(lambda s: s.paste.getLanguages())
        return ('\n'.join(result['langs']), result)

    def actionAddShortUrl(self):
        '''Add short-URL: <url>

        <url>        Short-URL to add
        '''
        url = self.args_.pop(0)
        result = self._callProxy(lambda s: s.paste.addShortURL(url))
        return (result['url'], result)

    def actionGetShortUrl(self):
        '''Resolve short-URL: <url>

        <url>        Short-URL to get clicks of
        '''
        url = self.args_.pop(0)
        result = self._callProxy(lambda s: s.paste.resolveShortURL(url))
        return (result['url'], result)

    def actionGetShortUrlClicks(self):
        '''Get clicks of short-URL: <url>

        <url>        Short-URL to get clicks of
        '''
        url = self.args_.pop(0)
        result = self._callProxy(lambda s: s.paste.ShortURLClicks(url))
        return (result['count'], result)

    def actionHelp(self):
        '''Print more verbose help about specific action: <action>

        <action>    Topic on which you need more verbose help.
        '''
        if len(self.args_) < 1:
            alias = "help"
        else:
            alias = self.args_.pop(0)

        if alias in actions:
            fun = actions[alias]
            print inspect.getdoc(self.__getattribute__(fun))
            print "\naliase: " + " ".join([i for i in actions_r[fun] if i != alias])
        else:
            print "Error: No such command - %s" % (alias)
            OPT_PARSER.print_usage()
        sys.exit(0)


# actionAddPaste -> [add, a]
actions_r = {}

# add -> actionAddPaste
# a   -> actionAddPaste
actions   = {}

# option parser
OPT_PARSER = None


##
# MAIN
##
if __name__ == "__main__":
    action_spec = ['actionAddPaste add a',
                   'actionDelPaste del d rm',
                   'actionGetPaste get g',
                   'actionGetLangs getlangs gl langs l',
                   'actionAddShortUrl addurl',
                   'actionGetShortUrl geturl',
                   'actionGetShortUrlClicks getclicks',
                   'actionHelp     help']
    for i in action_spec:
        aliases = i.split()
        cmd = aliases.pop(0)
        actions_r[cmd] = aliases
    for (k,v) in actions_r.items():
        for i in v:
            actions[i] = k

    usage = "usage: %prog [options] ACTION <args>\n\n" +\
            "actions:\n" +\
            "\n".join(["%12s\t%s" % (v[0], inspect.getdoc(getattr(Action, k)).split('\n')[0]) \
                for (k,v) in actions_r.items()])
    running_user = getpass.getuser()
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-n', '--name', default=running_user, help="Name of poster")
    parser.add_option('-e', '--expire', type=int, default=72, metavar='HOURS',
            help='Time at wich paste should expire')
    parser.add_option('-l', '--lang', default='Plain', help='Type of language to highlight')
    parser.add_option("-p", "--private", action="count", dest="private", default=0,
                        help='Create hidden paste'),
    parser.add_option('-s', '--server', default=DEFAULT_SERVER,
            help='Paste server')
    parser.add_option('-v', '--verbose', action='count', default=0, help='More output')
    (opts, args) = parser.parse_args()
    OPT_PARSER = parser

    if len(args) == 0:
        parser.error('Please provide me with an action')
    elif args[0] in actions:
        cmd = args.pop(0)
        action = Action(args, opts)
        try:
            (msg, ret) = action.call(actions[cmd])
            if opts.verbose == 0:
                print msg
            else:
                print ret
        except ActionFailedException, e:
            sys.stderr.write('Server Error: %s\n' % e.what())
            if opts.verbose >0:
                print e.dwhat()
            sys.exit(1)
    else:
        parser.error('Unknown action: %s' % args[0])
