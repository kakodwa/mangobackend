import base64


class Cursor:
    @staticmethod
    def encode(last_id: int):
        return base64.urlsafe_b64encode(str(last_id).encode()).decode()

    @staticmethod
    def decode(cursor: str):
        if not cursor:
            return None
        try:
            return int(base64.urlsafe_b64decode(cursor.encode()).decode())
        except:
            return None