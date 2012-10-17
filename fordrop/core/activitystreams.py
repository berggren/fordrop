import hashlib
import uuid

class ActivityStreams:
    def from_file(self, path):
        with open(path) as file:
            _file = file.read()
            md5 = hashlib.md5(_file).hexdigest()
            sha1 = hashlib.sha1(_file).hexdigest()
            sha256 = hashlib.sha256(_file).hexdigest()
            sha512 = hashlib.sha512(_file).hexdigest()
            ctph = ''
        activity = {}
        published = '1234'
        object = {}
        target = None
        actor = 'John Doe'
        object['objectType'] = 'fordrop:file'
        object['hash'] = {'md5': md5, 'sha1': sha1, 'sha256': sha256, 'sha512': sha512, 'ctph': ctph }
        object['id'] = uuid.uuid4().urn
        activity['published'] = published
        activity['verb'] = "post"
        activity['actor'] = actor
        activity['object'] = object
        return activity
    def from_django(self, actor=None, uuid=None, md5=None, sha1=None, sha256=None, sha512=None):
        ctph = ''
        activity = {}
        published = '1234'
        object = {}
        target = None
        object['objectType'] = 'fordropFile'
        object['hash'] = {'md5': md5, 'sha1': sha1, 'sha256': sha256, 'sha512': sha512, 'ctph': ctph }
        object['id'] = uuid
        activity['published'] = published
        activity['verb'] = "post"
        activity['actor'] = actor
        activity['object'] = object
        return activity


def is_activity(activity):
    if not isinstance(activity, dict):
        return False
    return True