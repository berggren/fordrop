import json
import requests

class FordropRestClient:
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
        r = requests.get(self.url + uri, headers=self.headers, verify=False)
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

