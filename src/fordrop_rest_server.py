from xml.etree import cElementTree as ET
import cherrypy
import json
import ConfigParser
from optparse import OptionParser
import sleekxmpp
from sleekxmpp.xmlstream.jid import JID
from sleekxmpp.plugins.xep_0004.stanza.form import Form

CONFIG_FILENAME = 'fordrop.cfg'
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILENAME)
parser = OptionParser(version="%prog 0.1")
parser.add_option('-u', '--username', action='store', dest='username', default=config.get("fordrop-client", "username"), help='username for fordrop-server')
parser.add_option('-k', '--api-key', action='store', dest='api_key', default=config.get("fordrop-client", "api-key"), help='api-key for fordrop-server')
parser.add_option('-j', '--jid', action='store', dest='jid', default=config.get("fordrop-server", "jid"), help='jid, XMPP username')
parser.add_option('-p', '--password', action='store', dest='password', default=config.get("fordrop-server", "password"), help='password, XMPP password')
parser.add_option('-s', '--server', action='store', dest='server', default=config.get("fordrop-server", "server"), help='XMPP server')
parser.add_option('--pubsub', action='store', dest='pubsub', default=config.get("fordrop", "pubsub"), help='XMPP pubsub service')
parser.add_option('--bind-address', action='store', dest='bind_address', default=config.get("fordrop-server", "bind_address"), help='Address to bind to (HTTP server)')
parser.add_option('--bind-port', action='store', dest='bind_port', default=config.getint("fordrop-server", "bind_port"), help='Port to bind to (HTTP server)')
(options, args) = parser.parse_args()

class XmppClient(sleekxmpp.ClientXMPP):
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

def login_required():
    username = cherrypy.request.headers.get('X-Fordrop-Username')
    api_key = cherrypy.request.headers.get('X-Fordrop-Api-Key')
    print username
    print api_key
    if username == options.username and api_key == options.api_key:
        return True
    raise cherrypy.HTTPError("401 Unauthorized")
cherrypy.tools.login_required = cherrypy.Tool('on_start_resource', login_required)

class NodeResource:
    def __init__(self, pubsub):
        self.nodes = {}
        self.pubsub = pubsub

    exposed = True

    def get_my_nodes(self, service):
        self.get_nodes(service)
        l = []
        for item in self.pubsub.get_affiliations(service).findall('{http://jabber.org/protocol/pubsub}pubsub'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub}affiliation'):
                if n.get('affiliation') == 'owner':
                    l.append({
                        'name': n.get('node'),
                        'title': self.nodes.get(n.get('node')),
                        'resource_uri': '/node/%s' % n.get('node')
                    })
        return json.dumps({'nodes': l})

    def get_node(self, service, node):
        if not self.nodes:
            self.get_nodes(service)
        xml = self.pubsub.get_node_config(options.pubsub, node=node).find('{http://jabber.org/protocol/pubsub#owner}pubsub/{http://jabber.org/protocol/pubsub#owner}configure/{jabber:x:data}x')
        form = Form(xml=xml)
        if not node in self.nodes.keys():
            raise cherrypy.HTTPError(404)
        return json.dumps({'node': [{
            'name': node,
            'title': self.nodes.get(node),
            'config': form.get_values(),
        }]})

    def get_nodes(self, service):
        for item in self.pubsub.get_nodes(service).findall('{http://jabber.org/protocol/disco#items}query'):
            for n in item.getiterator():
                self.nodes[n.get('node')] = n.get('name')
        return

    @cherrypy.tools.login_required()
    def GET(self, node=None):
        if node:
            return self.get_node(options.pubsub, node)
        else:
            return self.get_my_nodes(options.pubsub)

    @cherrypy.tools.login_required()
    def POST(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        config = Form(None, title='Node Config Form')
        config.addField('FORM_TYPE', 'hidden', value='http://jabber.org/protocol/pubsub#node_config')
        config.addField('pubsub#title', value=body.get('title'))
        config.addField('pubsub#access_model', value="whitelist")
        config.addField('pubsub#presence-subscribe', value="true")
        self.pubsub.create_node(options.pubsub, None, config=config)
        cherrypy.response.status = 201

    @cherrypy.tools.login_required()
    def DELETE(self, node=None):
        print "delete node"
        if not node:
            raise cherrypy.HTTPError(501)
        self.pubsub.delete_node(options.pubsub, node)
        cherrypy.response.status = 200

class AffiliationResource:
    def __init__(self, pubsub):
        self.pubsub = pubsub

    exposed = True

    def get_affiliations(self, service, node):
        members = []
        for item in self.pubsub.get_node_affiliations(service, node).findall('{http://jabber.org/protocol/pubsub#owner}pubsub'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#owner}affiliation'):
                if n.get('affiliation') == 'member':
                    members.append(n.get('jid'))
        return members

    @cherrypy.tools.login_required()
    def GET(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        return json.dumps({
            'node': node,
            'affiliations': self.get_affiliations(options.pubsub, node)
        })

    @cherrypy.tools.login_required()
    def POST(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        self.pubsub.modify_affiliations(options.pubsub, node,  body.get('affiliation'))
        print body.get('affiliation')
        cherrypy.response.status = 201

    @cherrypy.tools.login_required()
    def DELETE(self, node=None, jid=None):
        print "delete affiliation"
        if not node or not jid:
            raise cherrypy.HTTPError(501)
        self.pubsub.modify_affiliations(options.pubsub, node, [[jid, 'none']])
        print [[options.jid, 'outcast']]
        cherrypy.response.status = 200

class SubscriberResource:
    def __init__(self, pubsub):
        self.pubsub = pubsub

    exposed = True

    def get_subscribers(self, service, node):
        subscribers = []
        for item in self.pubsub.get_node_subscriptions(service, node).findall('{http://jabber.org/protocol/pubsub#owner}pubsub'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#owner}subscription'):
                subscribers.append(n.get('jid'))
        return subscribers

    @cherrypy.tools.login_required()
    def GET(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        return json.dumps({
            'node': node,
            'subscribers': self.get_subscribers(options.pubsub, node)
        })

class PublishResource:
    def __init__(self, pubsub):
        self.nodes = {}
        self.pubsub = pubsub
    exposed = True

    @cherrypy.tools.login_required()
    def POST(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        item = ET.Element('event')
        item.text = json.dumps(body.get('payload'))
        self.pubsub.publish(options.pubsub, node=body.get('node'), payload=item)
        cherrypy.response.status = 201

class Root:
    def __init__(self):
        self.xmpp = XmppClient(options.jid, options.password, verbose=True, priority=127)
        self.xmpp.run(options.server, threaded=True)
        self.pubsub = self.xmpp['xep_0060']

root = Root()
root.node = NodeResource(root.pubsub)
root.affiliations = AffiliationResource(root.pubsub)
root.subscribers = SubscriberResource(root.pubsub)
root.publish = PublishResource(root.pubsub)

if __name__ == '__main__':
    conf = {
        'global': {
            'server.socket_host': options.bind_address,
            'server.socket_port': options.bind_port,
            'server.thread_pool': 200,
            'server.socket_queue_size': 60,
            },
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            }
    }
    cherrypy.quickstart(root, '/', conf)
