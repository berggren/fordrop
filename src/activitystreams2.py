import uuid
import hashlib

class ActivityStreams:
    def file(self, path):
	with open(path) as file:
		_file = file.read()
		md5 = hashlib.md5(_file).hexdigest()
		sha1 = hashlib.sha1(_file).hexdigest()
		sha256 = hashlib.sha256(_file).hexdigest()
		sha512 = hashlib.sha512(_file).hexdigest()
        activity = {}
        published = '1234'
        object = {}
        target = None
        actor = 'johan'
        object['objectType'] = 'fordropFile'
        object['hash'] = {'md5': md5, 'sha1': sha1, 'sha256': sha256, 'sha512': sha512, 'ctph': '' }
        object['id'] = uuid.uuid4().urn
        activity['published'] = published
        activity['verb'] = "post"
        activity['actor'] = actor
        activity['object'] = object
        return activity

