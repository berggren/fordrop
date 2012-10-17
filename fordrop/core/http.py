import json
import cherrypy
import requests
from sleekxmpp.plugins.xep_0004.stanza.form import Form
from xml.etree import cElementTree as ET
from xmpp import Client

class NodeResource:
    def __init__(self, pubsub, args):
        self.nodes = {}
        self.pubsub = pubsub
        self.args = args

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
        xml = self.pubsub.get_node_config(self.args.pubsub_service, node=node).find('{http://jabber.org/protocol/pubsub#owner}pubsub/{http://jabber.org/protocol/pubsub#owner}configure/{jabber:x:data}x')
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

    def GET(self, node=None):
        if node:
            return self.get_node(self.args.pubsub_service, node)
        else:
            return self.get_my_nodes(self.args.pubsub_service)

    def POST(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        config = Form(None, title='Node Config Form')
        config.addField('FORM_TYPE', 'hidden', value='http://jabber.org/protocol/pubsub#node_config')
        config.addField('pubsub#title', value=body.get('title'))
        config.addField('pubsub#access_model', value="whitelist")
        config.addField('pubsub#presence-subscribe', value="true")
        self.pubsub.create_node(self.args.pubsub_service, body.get('name'), config=config)
        cherrypy.response.status = 201


    def DELETE(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        self.pubsub.delete_node(self.args.pubsub_service, node)
        cherrypy.response.status = 200

class AffiliationResource:
    def __init__(self, pubsub, args):
        self.pubsub = pubsub
        self.args = args

    exposed = True

    def get_affiliations(self, service, node):
        members = []
        for item in self.pubsub.get_node_affiliations(service, node).findall('{http://jabber.org/protocol/pubsub#owner}pubsub'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#owner}affiliation'):
                if n.get('affiliation') == 'member':
                    members.append(n.get('jid'))
        return members

    def GET(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        return json.dumps({
            'node': node,
            'affiliations': self.get_affiliations(self.args.pubsub_service, node)
        })

    def POST(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        self.pubsub.modify_affiliations(self.args.pubsub_service, node,  body.get('affiliation'))
        cherrypy.response.status = 201

    def DELETE(self, node=None, jid=None):
        if not node or not jid:
            raise cherrypy.HTTPError(501)
        self.pubsub.modify_affiliations(self.args.pubsub_service, node, [[jid, 'none']])
        self.pubsub.modify_subscriptions(self.args.pubsub_service, node, [[jid, 'none']])
        cherrypy.response.status = 200


class SubscriberResource:
    def __init__(self, pubsub, args):
        self.pubsub = pubsub
        self.args = args

    exposed = True

    def get_subscribers(self, service, node):
        subscribers = []
        for item in self.pubsub.get_node_subscriptions(service, node).findall('{http://jabber.org/protocol/pubsub#owner}pubsub'):
            for n in item.getiterator('{http://jabber.org/protocol/pubsub#owner}subscription'):
                subscribers.append(n.get('jid'))
        return subscribers

    def GET(self, node=None):
        if not node:
            raise cherrypy.HTTPError(501)
        return json.dumps({
            'node': node,
            'subscribers': self.get_subscribers(self.args.pubsub_service, node)
        })

    def POST(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        self.pubsub.subscribe(jid=body.get('service'), node=body.get('node'),
                subscribee=self.args.jid)
        cherrypy.response.status = 201

    def DELETE(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        self.pubsub.unsubscribe(jid=body.get('service'), node=body.get('node'),
                subscribee=self.args.jid)
        cherrypy.response.status = 200

class PublishResource:
    def __init__(self, pubsub, args):
        self.nodes = {}
        self.pubsub = pubsub
        self.args = args
    
    exposed = True

    def POST(self):
        body = json.loads(cherrypy.request.body.read(int(cherrypy.request.headers['Content-Length'])))
        item = ET.Element('event')
        item.text = json.dumps(body.get('payload'))
        self.pubsub.publish(self.args.pubsub_service, node=body.get('node'), payload=item)
        cherrypy.response.status = 201

class Root:
    def __init__(self, args):
        self.args = args
        self.xmpp = Client(self.args.jid, self.args.password, pubsub=False, priority=127)
        self.xmpp.run(args.server, threaded=True)
        self.pubsub = self.xmpp['xep_0060']

class RestClient:
    def __init__(self, url=None, username=None, api_key=None, verify=False):
        self.url = url
        self.verify = verify
        self.headers = {
            'content-type': 'application/json',
            'User-Agent': 'fordrop/client',
            'x-fordrop-username': username,
            'x-fordrop-api-key': api_key
        }

    def _http_get(self, uri):
        r = requests.get(self.url + uri, headers=self.headers, verify=self.verify)
        if r.status_code == requests.codes.ok:
            return json.loads(r.content)
        return r.status_code

    def _http_post(self, uri, data):
        r = requests.post(self.url + uri, json.dumps(data), headers=self.headers, verify=self.verify)
        return r

    def _http_delete(self, uri):
        r = requests.delete(self.url + uri, headers=self.headers, verify=self.verify)
        return r

    def list_nodes(self):
        nodes = self._http_get('/node')['nodes']
        return nodes

    def query_node(self, node=None):
        return json.dumps(self._http_get('/node/%s' % node))

    def create_node(self, title, name=None):
        data = {'title': title, 'name': name}
        return self._http_post('/node/', data)

    def delete_node(self, node=None):
        return self._http_delete('/node/%s' % node)

    def list_affiliations(self, node=None):
        affiliations = self._http_get('/affiliations/%s' % node)['affiliations']
        return affiliations

    def add_affiliation(self, node=None, jid=None):
        data = {'affiliation': [[jid, 'member']]}
        return self._http_post('/affiliations/%s' % node, data)

    def remove_affiliation(self, node=None, jid=None):
        return self._http_delete('/affiliations/%s/%s' % (node, jid))

    def list_subscribers(self, node=None):
        subscribers = self._http_get('/subscribers/%s' % node)['subscribers']
        return subscribers

    def subscribe(self, node=None, service=None, jid=None):
        data = {'node': node, 'service': service, 'jid': jid}
        return self._http_post('/subscribers/', data)

    def publish(self, node=None, payload=None):
        data = {'node': node, 'payload': payload}
        return self._http_post('/publish/', data)


