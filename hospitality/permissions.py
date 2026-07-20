from rest_framework.permissions import BasePermission


class IsHospitalityOwner(BasePermission):

    def has_permission(self, request, view):



        user = request.user



        if user.is_authenticated:
            print("USER DICT:", user.__dict__)

        user_type = getattr(user, "user_type", None)



        allowed = (
            user.is_authenticated and
            user_type == "hospitality_owner"
        )

        return allowed