from distutils.core import setup

config = {
    'description': 'fordrop - tool for a social CERT',
    'author': 'Johan Berggren',
    'url': 'https://fordrop.org',
    'download_url': 'https://fordrop.org',
    'author_email': 'jbn@klutt.se',
    'version': '0.2',
    'install_requires': ['requests', 'sleekxmpp', 'cherrypy'],
    'packages': ['fordrop', 'fordrop.core', 'fordrop.common', 'fordrop.plugins'],
    'scripts': ['bin/fordrop', 'bin/fordrop-broker', 'bin/fordrop-server'],
    'name': 'fordrop'
}

setup(**config)
