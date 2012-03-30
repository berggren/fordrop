import requests
import json
import ConfigParser
from optparse import OptionParser
from activitystreams2 import ActivityStreams
from fordrop_rest_client import get, post, delete

if __name__ == '__main__':
    CONFIG_FILENAME = 'fordrop.cfg'
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILENAME)
    parser = OptionParser(version="%prog 0.1")
    parser.add_option('-u', '--username', action='store', dest='username', default=config.get("fordrop-client", "username"), help='username for fordrop-server')
    parser.add_option('-k', '--api-key', action='store', dest='api_key', default=config.get("fordrop-client", "api-key"), help='api-key for fordrop-server')
    parser.add_option('--url', action='store', dest='url', default=config.get("fordrop-client", "base-url"), help='Base URL for fordrop-server')
    parser.add_option('-n', '--node', action='store', dest='node', help='Show configuration for node')
    parser.add_option('-t', '--title', action='store', dest='title', help='Title for node when creating')
    parser.add_option('-c', '--create', action='store_true', dest='create', help='Create new node')
    parser.add_option('-d', '--delete', action='store_true', dest='delete', help='Delete node, affiliation or subscription')
    parser.add_option('-q', '--query', action='store_true', dest='query', help='Use together with --node NODE to show configuration')
    parser.add_option('-H', '--human-readable', action='store_true', dest='human', help='Show title for node instead of actual name')
    parser.add_option('-a', '--affiliations', action='store_true', dest='affiliations', help='List affiliations for NODE')
    parser.add_option('-s', '--subscribers', action='store_true', dest='subscribers', help='List subscribers for NODE')
    parser.add_option('-f', '--file', action='store', dest='file', help='Extract info from file')
    parser.add_option('-p', '--publish', action='store_true', dest='publish', help='Publish to NODE (use with -n & -f)')
    parser.add_option('-j', '--jid', action='store', dest='jid', help='jid to add to affiliations on node')
    parser.add_option('--verify-ssl-cert', action='store_true', dest='verify_ssl_cert', help='Verify the certficate', default=config.getboolean("django", "verify_ssl"))
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', default=config.getboolean("fordrop", "verbose"))

    (options, args) = parser.parse_args()
    headers = {
        'content-type': 'application/json',
        'User-Agent': 'fordrop/client',
        'X-Fordrop-Username': options.username,
        'X-Fordrop-Api-Key': options.api_key
    }

    if options.verbose:
        print "--------------------------------------------------------"
        print "Connected to fordrop REST server"
        print "Location: %s" % options.url
        print "Authenticated as %s" % options.username
        print "--------------------------------------------------------"
        print ""

    try:
        # Create node
        if options.create and options.title:
            data = {'title': options.title}
            post('/node/', data, headers=headers)

        # Delete node
        if options.delete and options.node and not options.affiliations:
            delete('/node/%s' % options.node, headers=headers)

        # List nodes
        if options.query and not options.node:
            nodes = get('/node', headers=headers)['nodes']
            for node in nodes:
                if options.human:
                    print node['title'], '(%s)' % node['name']
                else:
                    print node['name']

        # Query node
        if options.query and options.node:
            print json.dumps(get('/node/%s' % options.node, headers=headers), indent=4)

        # Affiliations for node
        if options.affiliations and options.node and not options.jid:
            affiliations = get('/affiliations/%s' % options.node, headers=headers)['affiliations']
            for user in affiliations:
                print user

        # Add or delete jid as affiliate for node
        if options.affiliations and options.node and options.jid:
            if options.delete:
                delete('/affiliations/%s/%s' % (options.node, options.jid), headers=headers)
            else:
                data = {'affiliation': [[options.jid, 'member']]}
                post('/affiliations/%s' % options.node, data, headers=headers)

        # Subscribers on node
        if options.subscribers and options.node:
            subscribers = get('/subscribers/%s' % options.node, headers=headers)['subscribers']
            for user in subscribers:
                print user

        # Publish info on file to node
        make_activity = ActivityStreams()
        if options.publish and options.file and options.node:
            data = {'node': options.node, 'payload': make_activity.file(options.file)}
            result = post('/publish/', data, headers)
    except requests.exceptions.ConnectionError:
        print "Can't connect to fordrop daemon, is it running?"
