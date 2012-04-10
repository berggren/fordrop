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
            xmpp.add_handler("<message xmlns='jabber:client'><event xmlns='http://jabber.org/protocol/pubsub#event' /></message>", xmpp.pubsub_event_handler, name='Pubsub Event')

    def django(self):
        pubsub = self['xep_0060']
        headers = {'content-type': 'application/json', 'User-Agent': 'fordrop/beta', 'X_FORDROP_USERNAME': options.django_user, 'X_FORDROP_API_KEY': options.django_api_key}
        while True:
            try:
                files_to_publish = json.loads(requests.get(options.django_base_url + '/api/v1/full_file/?format=json&published=false', verify=options.django_verify_ssl, headers=headers).content)
                posts_to_publish = json.loads(requests.get(options.django_base_url + '/api/v1/full_post/?format=json&published=false', verify=options.django_verify_ssl, headers=headers).content)
                if files_to_publish['objects']:
                    for file in files_to_publish['objects']:
                        nodes = [x['node'] for x in file['boxes']]
                        if not nodes:
                            continue
                        activity = ActivityStreams()
                        item = ET.Element('event')
                        item.text = json.dumps(activity.file(file))
                        for node in nodes:
                            pubsub.publish(options.pubsub, node, payload=item)
                        requests.put(options.django_base_url + file['resource_uri'] + "?format=json", json.dumps({'published': 'true'}), verify=options.django_verify_ssl, headers=headers)
                        self.verbose_print("File %s published to %s" % (file['sha1'], nodes))
                if posts_to_publish['objects']:
                    for post in posts_to_publish['objects']:
                        nodes = [x['node'] for x in post['boxes']]
                        if not nodes:
                            continue
                        if post['file']:
                            target_type = 'file'
                            target = requests.get(options.django_base_url + '/api/v1/file/' + '?format=json&uuid=' + post['file']['uuid'], verify=options.django_verify_ssl, headers=headers)
                        else:
                            target_type = None
                            target = None
                        if target and target.status_code == 200:
                            target = target.content
                        activity = ActivityStreams()
                        item = ET.Element('event')
                        item.text = json.dumps(activity._http_post(post, target))
                        for node in nodes:
                            pubsub.publish(options.pubsub, node, payload=item)
                        requests.put(options.django_base_url + post['resource_uri'] + "?format=json", json.dumps({'published': 'true'}), verify=options.django_verify_ssl, headers=headers)
                        self.verbose_print("Post from %s published to %s" % (post['user']['profile']['name'], nodes))
            except ValueError: pass
            time.sleep(2)

    def pubsub_event_handler(self, xml):
        headers = {'content-type': 'application/json', 'User-Agent': 'fordrop/beta', 'X_FORDROP_USERNAME': options.django_user, 'X_FORDROP_API_KEY': options.django_api_key}
        for item in xml.findall('{http://jabber.org/protocol/pubsub#event}event/{http://jabber.org/protocol/pubsub#event}items/{http://jabber.org/protocol/pubsub#event}item'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#event}event'):
                activity = json.loads(n.text)
                print json.dumps(activity, indent=4)
                check_if_object_exists = None
                if activity['object']['objectType'] == "fordrop_file":
                    check_if_object_exists = requests.get(options.django_base_url + '/api/v1/file/' + '?format=json&uuid=' + activity['object']['id'], verify=options.django_verify_ssl, headers=headers)
                if activity['object']['objectType'] == "article":
                    check_if_object_exists = requests.get(options.django_base_url + '/api/v1/post/' + '?format=json&uuid=' + activity['object']['id'], verify=options.django_verify_ssl, headers=headers)
                if check_if_object_exists and check_if_object_exists.status_code == 200:
                    _r = json.loads(check_if_object_exists.content)
                    if _r['meta']['total_count'] > 0:
                        continue
                # Figure out the local user account + userprofile, create if missing
                user_resource_uri = None
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
                                requests.put(options.django_base_url + userprofile_resource_uri + "?format=json", json.dumps(p), verify=options.django_verify_ssl, headers=headers)
                                self.verbose_print("Created: %s and %s" % (user_resource_uri, userprofile_resource_uri))
                if user_resource_uri and activity['object']['objectType'] == "fordrop_file":
                    file_payload = {'user': user_resource_uri, 'uuid': activity['object']['id'], 'md5': activity['object']['hash']['md5'], 'sha1': activity['object']['hash']['sha1'], 'sha256': activity['object']['hash']['sha256'], 'sha512': activity['object']['hash']['sha512'], 'published': True, 'filename': activity['object']['hash']['sha1'], 'boxes': []}
                    file_uri = options.django_base_url + '/api/v1/file/' + "?format=json"
                    requests.post(file_uri, data=json.dumps(file_payload), verify=options.django_verify_ssl, headers=headers)
                    self.verbose_print("Created file: %s" % activity['object']['hash']['sha1'])
                elif user_resource_uri and activity['object']['objectType'] == "article":
                    if activity._http_get('target'):
                        r = requests.get(options.django_base_url + '/api/v1/file/' + '?format=json&uuid=' + activity['target']['object']['id'], verify=options.django_verify_ssl, headers=headers)
                        _r = json.loads(r.content)
                        if _r._http_get('objects'):
                            target_resource_uri = _r['objects'][0]['resource_uri']
                            post_payload = {'user': user_resource_uri, 'file': target_resource_uri, 'uuid': activity['object']['id'], 'post': activity['object']['content'], 'published': True, 'boxes': []}
                        else:
                            continue
                    else:
                        post_payload = {'user': user_resource_uri, 'uuid': activity['object']['id'], 'post': activity['object']['content'], 'published': True, 'boxes': []}
                    post_uri = options.django_base_url + '/api/v1/full_post/' + "?format=json"
                    requests.post(post_uri, data=json.dumps(post_payload), verify=options.django_verify_ssl, headers=headers)
                    self.verbose_print("Created post from %s" % activity['actor']['displayName'])
            else:
                continue

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

