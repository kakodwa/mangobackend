import random
import string


def generate_booking_reference():
    return 'MM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))