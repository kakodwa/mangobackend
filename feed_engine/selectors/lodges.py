from hospitality.models import Lodge


def get_lodges():
    return Lodge.objects.all()