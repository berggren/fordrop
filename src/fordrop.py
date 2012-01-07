#!/usr/bin/env python
__author__ = 'jbn'

import time
import requests
import json
import logging
import sleekxmpp
from sleekxmpp.xmlstream.jid import JID
import daemon
from xml.etree import cElementTree as ET
from activitystreams import ActivityStreams

logging.basicConfig(level=logging.ERROR, format="%(levelname)-8s %(message)s")

class FordropXmpp(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, verbose=False, priority=0):
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
        self.verbose_print("==> Connected!")
        self.verbose_print("==> Fetching roster")
        self.get_roster()
        self.verbose_print("==> Send priority %i for this connection" % self.priority)
        self.send_presence(ppriority=self.priority)
        if options.django:
            self.django()
        if options.listen:
            xmpp.add_handler("<message xmlns='jabber:client'><event xmlns='http://jabber.org/protocol/pubsub#event' /></message>", xmpp.pubsub_event_handler, name='Pubsub Event', threaded=False)

    def django(self):
        pubsub = self['xep_0060']
        headers = {'content-type': 'application/json', 'User-Agent': 'fordrop/beta', 'X_FORDROP_USERNAME': options.django_user, 'X_FORDROP_API_KEY': options.django_api_key}
        while True:
            uri = "/api/v1/file/?format=json&published=false"
            url = options.django_base_url + uri
            try:
                result = json.loads(requests.get(url, verify=options.django_verify_ssl, headers=headers).content)
                for file in result['objects']:
                    nodes = []
                    for box in file['boxes']:
                        nodes.append(box['node'])
                    file_uri = options.django_base_url + file['resource_uri'] + "?format=json"
                    activity = ActivityStreams()
                    file_activity = activity.file(file)
                    item = ET.Element('event')
                    item.text = json.dumps(file_activity)
                    for node in nodes:
                        pubsub.publish(options.pubsub, node, payload=item)
                    requests.put(file_uri, json.dumps({'published': 'true'}), verify=options.django_verify_ssl, headers=headers)
                    self.verbose_print("File published to nodes %s and database object updated" % nodes)
            except ValueError: pass
            time.sleep(10)

    def pubsub_event_handler(self, xml):
        headers = {'content-type': 'application/json', 'User-Agent': 'fordrop/beta', 'X_FORDROP_USERNAME': options.django_user, 'X_FORDROP_API_KEY': options.django_api_key}
        for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}items/{http://jabber.org/protocol/pubsub#event}item'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#event}event'):
                activity = json.loads(n.text)

                check_if_file_exists = requests.get(options.django_base_url + '/api/v1/file/' + '?format=json&uuid=' + activity['object']['id'], verify=options.django_verify_ssl, headers=headers)
                if check_if_file_exists.status_code == 200:
                    _r = json.loads(check_if_file_exists.content)
                    if _r['meta']['total_count'] > 0:
                        continue
                r = requests.get(options.django_base_url + '/api/v1/user/' + '?format=json&username=' + activity['actor']['id'], verify=options.django_verify_ssl, headers=headers)
                # Figure out the local user account + userprofile, create if missing
                r = requests.get(options.django_base_url + '/api/v1/user/' + '?format=json&username=' + activity['actor']['id'], verify=options.django_verify_ssl, headers=headers)
                if r.status_code == 200:
                    _r = json.loads(r.content)
                    if _r['meta']['total_count'] > 0:
                        user_resource_uri = _r['objects'][0]['resource_uri']
                        userprofile_resource_uri = _r['objects'][0]['profile']['resource_uri']
                    else:
                        user_uri = options.django_base_url + '/api/v1/bare_user/' + "?format=json"
                        user_payload = {'username': activity['actor']['id'], 'is_active': False}
                        create_user = requests.post(user_uri, data=json.dumps(user_payload), verify=options.django_verify_ssl, headers=headers)
                        if create_user.status_code == 201:
                            r = requests.get(options.django_base_url + '/api/v1/user/' + '?format=json&username=' + activity['actor']['id'], verify=options.django_verify_ssl, headers=headers)
                            _r = json.loads(r.content)
                            if _r['meta']['total_count'] > 0:
                                user_resource_uri = _r['objects'][0]['resource_uri']
                                userprofile_resource_uri = _r['objects'][0]['profile']['resource_uri']
                                # Update the local profile with data from the activity
                                p = {
                                    'name': activity['actor']['displayName'],
                                    'location': activity['actor']['location'],
                                    'web': activity['actor']['web'],
                                    'bio': activity['actor']['bio'],
                                    'uuid': activity['actor']['id'],
                                }
                                updated_profile = requests.put(options.django_base_url + userprofile_resource_uri + "?format=json", json.dumps(p), verify=options.django_verify_ssl, headers=headers)
                                print "Created:", user_resource_uri, userprofile_resource_uri
                file_payload = {'user': user_resource_uri, 'uuid': activity['object']['id'], 'md5': activity['object']['hash']['md5'], 'sha1': activity['object']['hash']['sha1'], 'sha256': activity['object']['hash']['sha256'], 'sha512': activity['object']['hash']['sha512'], 'published': True, 'filename': activity['object']['hash']['sha1'], 'boxes': []}
                file_uri = options.django_base_url + '/api/v1/file/' + "?format=json"
                create_file = requests.post(file_uri, data=json.dumps(file_payload), verify=options.django_verify_ssl, headers=headers)
                print "Created file: %s" % activity['object']['hash']['sha1']
                #print "%s recieved event: %s" % (self.jid, json.dumps(json.loads(n.text), indent=4))

    def verbose_print(self, msg):
        if self.verbose:
            print msg

if __name__ == "__main__" :
    import ConfigParser
    from optparse import OptionParser
    import getpass
    CONFIG_FILENAME = 'fordrop.cfg'
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILENAME)
    parser = OptionParser(version="%prog 0.1")
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=config.getboolean("fordrop", "verbose"))
    parser.add_option('-q', '--quiet', action='store_false', dest='verbose', default=config.getboolean("fordrop", "verbose"))
    parser.add_option('-d', '--daemon', action='store_true', dest='daemon', default=config.getboolean("fordrop", "daemon"))
    parser.add_option('-j', '--jid', action='store', dest='jid', default=config.get("fordrop", "jid"))
    parser.add_option('-p', '--password', action='store', dest='password', default=config.get("fordrop", "password"))
    parser.add_option('-s', '--server', action='store', dest='server', help='XMPP server', default=config.get("fordrop", "server"))
    parser.add_option('-u', '--pubsub', action='store', dest='pubsub', help='Pubsub service, ex pubsub.example.com', default=config.get("fordrop", "pubsub"))
    parser.add_option('-l', '--log', action='store_true', dest='log', help='Log to syslog', default=config.getboolean("fordrop", "log"))
    parser.add_option('--no-events', action='store_true', dest='no_events', help=("Don't process pubsub events"), default=config.getboolean("fordrop", "no_events"))
    parser.add_option('-o', '--priority', action='store', type="int", dest='priority', help='Priority for this connection', default=config.getint("fordrop", "priority"))
    parser.add_option('-L', '--listen', action='store_true', dest='listen', help='Listen for events', default=config.getboolean("fordrop", "listen"))
    parser.add_option('--django', action='store_true', dest='django', help='Get from django', default=config.getboolean("fordrop", "django"))
    parser.add_option('--django-user', action='store', dest='django_user', help='Django user', default=config.get("django", "user"))
    parser.add_option('--django-api-key', action='store', dest='django_api_key', help='Django API-key', default=config.get("django", "api_key"))
    parser.add_option('--django-base-url', action='store', dest='django_base_url', help='Django base URL, ex http://127.0.0.1', default=config.get("django", "base_url"))
    parser.add_option('--django-verify-ssl', action='store_true', dest='django_verify_ssl', help='Verify the certficate', default=config.getboolean("django", "verify_ssl"))
    (options, args) = parser.parse_args()
    if not options.jid:
        parser.error("You need to specify a jid")
    if not options.password:
        options.password = getpass.getpass("Enter password for %s: " % options.jid)
    jid = JID(options.jid)
    xmpp = FordropXmpp(jid, options.password, options.verbose, options.priority)
    if options.daemon:
        with daemon.DaemonContext():
            xmpp.run(options.server)
    else:
        xmpp.run(options.server)
