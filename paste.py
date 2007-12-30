#!/usr/bin/python

import sys
import xmlrpclib
import optparse
from pprint import pprint


class ActionFailedException(Exception):
    def __init__(self, errormsg, ret):
        Exception.__init__(self, errormsg, ret)
    def what(self):
        return self.args[0]
    def dwhat(self):
        return self.args[1]


class Action(object):
    def __init__(self, cmd, args, opts):
        self.cmd_  = cmd
        self.args_ = args
        self.opts_ = opts

    def _createProxy(self):
        return xmlrpclib.ServerProxy(self.opts_.server)

    def _callProxy(self, functor, server=None):
        if server is None:
            server = self._createProxy()
        ret = functor(server)
        if ret['rc'] != 0:
            raise ActionFailedException(ret['statusmessage'], ret)
        return ret

    def call(self, method):
        return self.__getattribute__(method)()

    def actionAddPaste(self):
        server = self._createProxy()
        o = self.opts_
        code = self.args_
        if len(self.args_) == 0:
            code = [ i.strip() for i in sys.stdin.readlines() ]
        code = '\n'.join(code)
        result = self._callProxy(lambda s: s.paste.addPaste(code, o.name, o.expire * 3600, o.lang),
                            server)
        return (result['statusmessage'], result)

    def actionDelPaste(self):
        digest = self.args_.pop(0)

        result = self._callProxy(lambda s: s.paste.deletePaste(digest))
        return (result['statusmessage'], result)

    def actionGetPaste(self):
        id = self.args_.pop(0)

        result = self._callProxy(lambda s: s.paste.getPaste(id))
        return (result['code'], result)

    def actionGetLangs(self):
        result = self._callProxy(lambda s: s.paste.getLanguages())
        return ('\n'.join(result['langs']), result)


##
# MAIN
##
if __name__ == "__main__":
    action_spec = ['actionAddPaste add a',
                   'actionDelPaste del d rm',
                   'actionGetPaste get g',
                   'actionGetLangs getlangs gl langs l' ]
    actions = {}
    for i in action_spec:
        tmp = i.split()
        cmd = tmp.pop(0)
        for i in tmp:
            actions[i] = cmd

    parser = optparse.OptionParser(usage="usage: %prog [options] ACTION <args>")
    parser.add_option('-n', '--name', default='anonymous', help="Name of poster")
    parser.add_option('-e', '--expire', type=int, default=72, metavar='HOURS',
            help='Time at wich the paste should expire')
    parser.add_option('-l', '--lang', default='Plain', help='Type of language to highlight')
    parser.add_option('-s', '--server', default='http://paste.snow-crash.org/server.pl',
            help='Paste server')
    parser.add_option('-v', '--verbose', action='count', default=0, help='More output')
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('Please provide me with an action')
    elif args[0] in actions:
        cmd = args.pop(0)
        action = Action(cmd, args, opts)
        try:
            (msg, ret) = action.call(actions[cmd])
            if opts.verbose == 0:
                print msg
            else:
                pprint(ret)
        except ActionFailedException, e:
            sys.stderr.write('Server Error: %s\n' % e.what())
            if opts.verbose >0:
                pprint(e.dwhat())
            sys.exit(1)
    else:
        parser.error('Unknown action: %s' % args[0])
