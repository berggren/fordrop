import json
import requests

baseurl = 'http://127.0.0.1:8080/api/v1/'
headers = {'content-type': 'application/json'}

activity = json.dumps({
    "published": "2012-04-25T08:51:38.031593+00:00",
    "verb": "post",
    "actor": {
        "web": "http://jbn.klutt.se/",
        "displayName": "Johan Berggren",
        "bio": "Foobar",
        "location": "Sweden",
        "id": "urn:uuid:5ad9cf86-deb5-4ea9-982d469b",
        "objectType": "person"
    },
    "object": {
        "objectType": "fordropFile",
        "hash": {
            "sha256": "bbc716c8b3df5cc31b52160ddb4e7c2efde37ec0713f56c6193604be8a642627",
            "sha1": "44cdcbea81e3bc6af2450c84568559b605da324f",
            "sha512": "1d06b333ffb01d6cda0b66217d95c074ab6a66a6455dae0b23ec26dc6df2397a67a04a0356972f7dbaae70140471bac4f0c7ada111e38e0a29414824109e0e4e",
            "md5": "7307472f473a58602cdf14b586389b21"
        },
        "id": "urn:uuid:a622f8f4-0a39-a29",
        "description": ""
    }
})

def get_or_create_file(activity):
    activity_json = json.loads(activity)
    file = activity_json.get('object')
    hashes = file.get('hash')
    if not file.get('objectType') == 'fordropFile':
        return
    user = get_or_create_user(activity)
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
    user_payload = {'username': actor.get('id'), 'is_active': False}
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

print plugin(activity)