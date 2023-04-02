def generate_message_key(key: str):
    return hex(hash(key))[2:]
