class ActivityStreams:
    def file(self, obj):
        activity = {}
        published = obj['time_created']
        object = {}
        target = None
        actor = self.person(obj['user'])
        object['objectType'] = 'fordrop_file'
        object['hash'] = {'md5': obj['md5'], 'sha1': obj['sha1'], 'sha256': obj['sha256'], 'sha512': obj['sha512'], 'ctph': obj['ctph'] }
        object['id'] = obj['uuid']
        activity['published'] = published
        activity['verb'] = "post"
        activity['actor'] = actor
        activity['object'] = object
        if target:
            activity['target'] = target
        return activity

    def post(self, obj):
        activity = {}
        published = obj['time_created']
        object = {}
        target = None
        actor = self.person(obj['user'])
        object['objectType'] = 'article'
        object['id'] = obj['uuid']
        object['content'] = obj['post']
        activity['published'] = published
        activity['verb'] = "post"
        activity['actor'] = actor
        activity['object'] = object
        if target:
            activity['target'] = target
        return activity

    def person(self, obj):
        object = {}
        object['objectType'] = 'person'
        object['id'] = obj['profile']['uuid']
        object['published'] = obj['profile']['time_created']
        object['updated'] = obj['profile']['time_updated']
        object['url'] = obj['profile']['web']
        object['image'] = obj['profile']['avatar']
        object['displayName'] = obj['profile']['name']
        object['email'] = obj['profile']['email']
        object['location'] = obj['profile']['location']
        object['web'] = obj['profile']['web']
        object['bio'] = obj['profile']['bio']
        return object
