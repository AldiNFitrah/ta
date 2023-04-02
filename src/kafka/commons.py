import json


def serialize_json(obj):
    return json.dumps(obj).encode('utf-8')


def deserialize_json(obj: bytes):
    decoded = obj.decode('utf-8')

    try:
        return json.loads(decoded)

    except:
        return decoded
