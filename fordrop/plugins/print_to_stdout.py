import json

def plugin(activity):
    print json.dumps(activity, indent=2)
    return True