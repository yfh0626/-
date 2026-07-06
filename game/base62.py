ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def encodebytes(data: bytes) -> str:
    if not data:
        return ""

    leading_zeroes = len(data) - len(data.lstrip(b"\x00"))
    value = int.from_bytes(data, "big")
    encoded = []

    while value:
        value, remainder = divmod(value, 62)
        encoded.append(ALPHABET[remainder])

    body = "".join(reversed(encoded)) if encoded else ALPHABET[0]
    return (ALPHABET[0] * leading_zeroes) + body
