#!/usr/bin/python

import sys
import xmlrpclib
import optparse


class ActionFailedException(Exception):
    def __init__(self, errormsg):
        Exception.__init__(self)
        self.errormsg_ = errormsg
    def what(self):
        return self.errormsg_


class Action(object):
    def __init__(self, cmd, args, opts):
        self.cmd_  = cmd
        self.args_ = args
        self.opts_ = opts

    def _createProxy(self):
        return xmlrpclib.ServerProxy(self.opts_.server)

    def _callProxy(self, functor, server=None):
        if not server: server = self._createProxy()
        ret = functor(server)
        if ret['rc'] != 0:
            raise ActionFailedException(ret['statusmessage'])
        return ret

    def call(self, method):
        self.__getattribute__(method)()

    def actionAddPaste(self):
        server = self._createProxy(self.opts_)
        o = self.opts_
        code = self.args_
        if len(self.args_) == 0:
            code = [ i.strip() for i in sys.stdin.readlines() ]
        code = '\n'.join(code)
        result = _callProxy(lambda server: server.paste.addPaste(code, o.name, o.expire * 3600, o.lang),
                            server)
        print result

    def actionDelPaste(self):
        digest = self.args_.pop(0)

        server = _createProxy(self.opts_)
        result = server.paste.deletePaste(digest)

    def actionGetPaste(self):
        id = self.args_.pop(0)

        result = self._callProxy(lambda server: server.paste.getPaste(id))
        print result

    def actionGetLangs(self):
        result = self._callProxy(lambda server: server.paste.getLanguages())
        print result


##
# MAIN
##
if __name__ == "__main__":
    action_spec = ['add actionAddPaste', 'del rm actionDelPaste', 'get actionGetPaste',
                   'getlangs langs actionGetLangs' ]
    actions = {}
    for i in action_spec:
        tmp = i.split()
        cmd = tmp.pop()
        for i in tmp:
            actions[i] = cmd

    parser = optparse.OptionParser(usage="usage: %prog [options] ACTION <args>")
    parser.add_option('-n', '--name', default='anonymous', help="Name of poster")
    parser.add_option('-e', '--expire', type=int, default=72, metavar='HOURS',
            help='Time at wich the paste should expire')
    parser.add_option('-l', '--lang', default='plain', help='Type of language to highlight')
    parser.add_option('-s', '--server', default='http://paste.snow-crash.org/server.pl',
            help='Paste server')
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('Please provide me with an action')
    elif args[0] in actions:
        cmd = args.pop(0)
        action = Action(cmd, args, opts)
        try:
            action.call(actions[cmd])
        except ActionFailedException, e:
            print 'Server Error:', e.what()
    else:
        parser.error('Unknown action: %s' % args[0])
