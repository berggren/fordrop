from distutils.core import setup

config = {
    'description': 'fordrop - tool for a social CERT',
    'author': 'Johan Berggren',
    'url': 'https://fordrop.org',
    'download_url': 'https://fordrop.org',
    'author_email': 'jbn@nordu.net',
    'version': '0.1.1',
    'install_requires': ['requests', 'sleekxmpp', 'cherrypy'],
    'packages': ['fordrop', 'fordrop.plugins'],
    'scripts': ['bin/fordrop', 'bin/fordropd', 'bin/fordrop-rest-server'],
    'name': 'fordrop'
}

setup(**config)