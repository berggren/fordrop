#!/usr/bin/env python
import json
import logging
import sleekxmpp
import argparse
import ConfigParser
from sleekxmpp.jid import JID
import sys
from lib.fordrop.core.activitystreams import is_activity
from lib.fordrop.core.client import FordropXmppClient
from lib.fordrop.core.utils import init_logging

log = logging.getLogger()
sleekxmpp_log = logging.getLogger("sleekxmpp")
sleekxmpp_log.setLevel(logging.ERROR)

def main():
    jid = JID(args.jid)
    xmpp = FordropXmppClient(
            jid, 
            args.password, 
            args.verbose,
            int(args.priority),
            plugins=config.get('fordropd', 'plugins').split(','))
    xmpp.run(args.server)

if __name__ == "__main__" :
    init_logging()
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument("-c", "--config",
        help="Specify config file",
        metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()
    
    if args.config:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items("fordropd"))
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
    main()
