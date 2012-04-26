import json

def plugin(activity):
    print json.dumps(json.loads(activity), indent=2)
    return True