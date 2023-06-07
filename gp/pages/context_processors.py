
from django.contrib.auth.models import Group

def get_user_groups(request):
    if request.user.is_authenticated:
        groups = request.user.groups.all()
        for group in groups:
            if group.name == 'Coordinators':
                return {'get_user_groups': True}
    return {'get_user_groups': False}
        