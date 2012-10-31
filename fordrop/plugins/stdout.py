# Copyright (C) 2012 NORDUnet A/S.
# This file is part of fordrop - https://fordrop.org
# See the file 'docs/LICENSE' for copying permission.

import json

def plugin(activity):
    print json.dumps(json.loads(activity), indent=2)
    return True
