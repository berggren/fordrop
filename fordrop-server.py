#!/usr/bin/env python
import sys
import logging
import argparse
import ConfigParser
import cherrypy
from lib.fordrop.core.utils import init_logging, login_required
from lib.fordrop.core.http import NodeResource, AffiliationResource, SubscriberResource, PublishResource, Root

def main():
    root = Root(args)
    root.node = NodeResource(root.pubsub, args)
    root.affiliations = AffiliationResource(root.pubsub, args)
    root.subscribers = SubscriberResource(root.pubsub, args)
    root.publish = PublishResource(root.pubsub, args)
    conf = {
        'global': {
            'server.socket_host': args.bind_address,
            'server.socket_port': int(args.bind_port),
            'server.thread_pool': 200,
            'server.socket_queue_size': 60,
            },
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.login_required.on': True,
            'tools.login_required.args': args
            }
    }
    cherrypy.quickstart(root, '/', conf)

if __name__ == '__main__':
    log = logging.getLogger()
    sleekxmpp_log = logging.getLogger("sleekxmpp")
    sleekxmpp_log.setLevel(logging.ERROR)
    init_logging()
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument("-c", "--config",
            help="Specify config file",
            metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    if args.config:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items("fordrop-server"))
    else:
        log.error("No configuration file found, you must use --config FILE")
        sys.exit(1)
    parser = argparse.ArgumentParser(
            parents=[conf_parser],
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_defaults(**defaults)
    parser.add_argument("-d", "--debug",
            help="Debug",
            action="store_true",
            required=False)
    args = parser.parse_args(remaining_argv)
    if args.debug:
        sleekxmpp_log.setLevel(logging.DEBUG)
    
    cherrypy.tools.login_required = cherrypy.Tool('on_start_resource', login_required)
    main()



