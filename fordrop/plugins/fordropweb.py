# Copyright (C) 2012 NORDUnet A/S.
# This file is part of fordrop - https://fordrop.org
# See the file 'docs/LICENSE' for copying permission.

import json
import requests
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('/etc/fordrop.cfg')

baseurl = config.get('fordropweb', 'apiurl')
headers = {'content-type': 'application/json', 'Authorization': 'ApiKey %s:%s' % (config.get('fordrop-plugin-fordropweb', 'username'), config.get('fordrop-plugin-fordropweb', 'api_key'))}

def get_or_create_file(activity):
    activity_json = json.loads(activity)
    file = activity_json.get('object')
    hashes = file.get('hash')
    if not file.get('objectType') == 'fordropFile':
        return
    profile = get_or_create_user(activity)
    user = profile.get('user')
    if not user:
        return
    def check_if_file_exist(file):
        r = requests.get(baseurl + 'file/', params={'uuid': file.get('id')})
        result = json.loads(r.content)
        if not result.get('objects'):
            return None
        return r
    file_exists = check_if_file_exist(file)
    if file_exists:
        return json.loads(file_exists.content).get('objects')[0]
    file_payload = json.dumps({
        'user': user.get('resource_uri'),
        'md5': hashes.get('md5', ''),
        'sha1': hashes.get('sha1', ''),
        'sha256': hashes.get('sha256', ''),
        'sha512': hashes.get('sha512', ''),
        'uuid': file.get('id'),
        'description': file.get('description', '')
    })
    r = requests.post(baseurl + 'file/', data=file_payload, headers=headers)
    if r.status_code == requests.codes.ok or r.status_code is 201:
        file = requests.get(baseurl + 'file/', params={'uuid': file.get('id')})
    return json.loads(file.content).get('objects')[0]

def get_or_create_user(activity):
    activity = json.loads(activity)
    actor = activity.get('actor')
    if not actor.get('objectType') == 'person':
        return
    def check_if_user_exist(actor):
        r = requests.get(baseurl + 'userprofile/', params={'uuid': actor.get('id')})
        result = json.loads(r.content)
        if not result.get('objects'):
            return None
        return r
    user_exists = check_if_user_exist(actor)
    if user_exists:
        return json.loads(user_exists.content).get('objects')[0]
    user_payload = {'username': actor.get('id'), 'is_active': True}
    profile_payload = json.dumps({
                'user': user_payload,
                'name': actor.get('displayName', ''),
                'location': actor.get('location', ''),
                'web': actor.get('web', ''),
                'bio': actor.get('bio', ''),
                'uuid': actor.get('id', '')
        })
    r = requests.post(baseurl + 'userprofile/', data=profile_payload, headers=headers)
    if r.status_code == requests.codes.ok or r.status_code is 201:
        user = requests.get(baseurl + 'userprofile/', params={'uuid': actor.get('id')})
    return json.loads(user.content).get('objects')[0]

def plugin(activity):
    activity_json = json.loads(activity)
    if activity_json.get('verb') == 'post':
        object_type = activity_json.get('object')['objectType']
        if object_type == 'fordropFile':
            file = get_or_create_file(activity)
            if not file:
                return
            return True
    return True
