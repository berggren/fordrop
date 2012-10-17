import logging
import cherrypy

log = logging.getLogger()

def init_logging():
    formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    log.addHandler(sh)
    log.setLevel(logging.INFO)

def login_required(args):
    username = cherrypy.request.headers.get('X-Fordrop-Username')
    api_key = cherrypy.request.headers.get('X-Fordrop-Api-Key')
    if username == args.username and api_key == args.api_key:
        return True
    raise cherrypy.HTTPError("401 Unauthorized")


