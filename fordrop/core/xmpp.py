# Copyright (C) 2012 NORDUnet A/S.
# This file is part of fordrop - https://fordrop.org
# See the file 'docs/LICENSE' for copying permission.

import json
import sleekxmpp
from activitystreams import is_activity
from sleekxmpp.jid import JID
import logging

class Client(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, pubsub=False, priority=0, plugins=[]):
        jid = JID(jid)
        sleekxmpp.ClientXMPP.__init__(self, jid.full, password)
        self.jid = jid.full
        self.priority = priority
        self.pubsub = pubsub
        self.register_plugin('xep_0004')
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0060')
        self.add_event_handler("session_start", self.start)
        self.plugins = plugins
        self.active_plugins = {}
        self.log = logging.getLogger()
        if self.pubsub:
            for plugin in self.plugins:
                self.active_plugins[plugin] = __import__('lib.fordrop.plugins.%s' % plugin, fromlist=['plugins'])

    def run(self, server, threaded=False):
        self.log.info('Connecting to %s' % self.server)
        self.connect((server, 5222))
        self.process(threaded=threaded)

    def start(self, event):
        self.log.info('Get roster')
        self.get_roster()
        self.log.info('Set priority to %s' % self.priority)
        self.send_presence(ppriority=self.priority)
        self.log.info('Ok, ready! Waiting for requests..')
        if self.pubsub:
            self.log.info('[XMPP] Add handler for pubsub events')
            self.add_handler("<message xmlns='jabber:client'><event xmlns='http://jabber.org/protocol/pubsub#event' /></message>", self.pubsub_event_handler, name='Pubsub Event')

    def pubsub_event_handler(self, xml):
        for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}items/{http://jabber.org/protocol/pubsub#event}item'):
            for event in item.getiterator('{http://jabber.org/protocol/pubsub#event}event'):
                activity = json.loads(event.text)
                if is_activity(activity):
                    for name, plugin in self.active_plugins.items():
                        plugin.plugin(event.text)



