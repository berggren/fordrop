import logging
import sleekxmpp
from sleekxmpp.xmlstream.jid import JID

logging.basicConfig(level=logging.ERROR, format="%(levelname)-8s %(message)s")

class FordropXmpp(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, verbose=False, priority=0):
        jid = JID(jid)
        sleekxmpp.ClientXMPP.__init__(self, jid.full, password)
        self.jid = jid.full
        self.priority = priority
        self.verbose = verbose
        self.register_plugin('xep_0004')
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0060')
        self.add_event_handler("session_start", self.start)

    def run(self, server, threaded=False):
        self.verbose_print("==> Connecting to %s as %s.." % (server, self.jid))
        self.connect((server, 5222))
        self.process(threaded=threaded)

    def start(self, event):
        if event:
            self.verbose_print("==> Got event " + event)
        self.verbose_print("==> Connected!")
        self.verbose_print("==> Fetching roster")
        self.get_roster()
        self.verbose_print("==> Send priority %i for this connection" % self.priority)
        self.send_presence(ppriority=self.priority)

    def verbose_print(self, msg):
        if self.verbose:
            print msg
