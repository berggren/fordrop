#!/usr/bin/env python
# Copyright (C) 2012 NORDUnet A/S.
# This file is part of fordrop - https://fordrop.org
# See the file 'docs/LICENSE' for copying permission.

import sys
import argparse
import ConfigParser
import json
import logging

from lib.fordrop.core.client import FordropRestClient
from lib.fordrop.core.activitystreams import ActivityStreams
from lib.fordrop.core.utils import init_logging

log = logging.getLogger()
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def main():
    fordrop = FordropRestClient(
            url=args.url, 
            username=args.username, 
            api_key=args.apikey, 
            verify=False
    )
    if args.debug:
        requests_log.setLevel(logging.DEBUG)
    if args.list:
        for node in fordrop.list_nodes():
            print "[%s] %s" % (node['name'], node['title'])
    if args.query:
        print json.dumps(
                json.loads(fordrop.query_node(node=args.node)),
                indent=2)
        print "Members: ", [member for member in
                fordrop.list_affiliations(node=args.node)]
        print "Subscribers: ", [subscriber for subscriber in
                fordrop.list_subscribers(node=args.node)]
    if args.create_node:
        print fordrop.create_node(
                title=args.create_node)
    if args.delete_node:
        print fordrop.delete_node(
                node=args.delete_node)
    if args.add_member:
        print fordrop.add_affiliation(
                node=args.node,
                jid=args.add_member)
    if args.remove_member:
        print fordrop.remove_affiliation(
                node=args.node, 
                jid=args.remove_member)
    if args.subscribe:
        print fordrop.subscribe(
                node=args.node, 
                service=args.remote_service)
    if args.publish:
        activity = ActivityStreams()
        payload = activity.from_file(args.publish)
        fordrop.publish(node=args.node, payload=payload)

if __name__ == '__main__':
    init_logging()
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument("-c", "--config",
            help="Specify config file",
            metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    if args.config:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items("fordrop"))
    else:
        log.error("No configuration file found, you must use --config FILE")
        sys.exit(1)
    parser = argparse.ArgumentParser(
        parents=[conf_parser],
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.set_defaults(**defaults)
    parser.add_argument("--list", 
            help="List nodes", 
            action="store_true", 
            required=False)
    parser.add_argument("--query", 
            help="Query node", 
            action="store_true",
            required=False)
    parser.add_argument("--create-node", 
            help="Create node", 
            action="store",
            metavar="NAME",
            required=False)
    parser.add_argument("--delete-node", 
            help="Delete node", 
            action="store",
            metavar="NODE",
            required=False)
    parser.add_argument("--add-member", 
            help="Add member to node, ex john@example.com", 
            action="store",
            metavar="USER",
            required=False)
    parser.add_argument("--remove-member", 
            help="Remove member from node, ex john@example.com", 
            action="store",
            metavar="USER",
            required=False)
    parser.add_argument("--node", 
            help="Node to operate on", 
            action="store",
            metavar="NODE",
            required=False)
    parser.add_argument("--publish", "-p", 
            help="Publish FILE metadata to NODE", 
            action="store",
            metavar="FILE",
            required=False)
    parser.add_argument("--subscribe", 
            help="Subscribe to NODE at remote fordrop server", 
            action="store_true",
            required=False)
    parser.add_argument("--remote-service", 
            help="Remote fordrop server, ex pubsub.example.com", 
            action="store",
            metavar="REMOTE SERVICE",
            required=False)
    parser.add_argument("--debug",
            help="Debug output",
            action="store_true",
            required=False,
            default=False) 
    args = parser.parse_args(remaining_argv)
    main()
