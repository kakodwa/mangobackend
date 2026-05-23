import json

from django.core.signing import (
    TimestampSigner,
    BadSignature,
    SignatureExpired,
)

signer = TimestampSigner()


def verify_qr_token(token, max_age=86400):
    try:
        value = signer.unsign(token, max_age=max_age)

        data = json.loads(value)

        return data

    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return None