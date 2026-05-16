from rest_framework.permissions import BasePermission


class IsHospitalityOwner(BasePermission):

    def has_permission(self, request, view):

        print("\n🔥 ===== PERMISSION DEBUG =====")

        user = request.user

        print("🔥 USER:", user)
        print("🔥 AUTH:", user.is_authenticated)

        if user.is_authenticated:
            print("🔥 USER DICT:", user.__dict__)

        user_type = getattr(user, "user_type", None)

        print("🔥 USER TYPE:", user_type)

        allowed = (
            user.is_authenticated and
            user_type == "hospitality_owner"
        )

        print("🔥 ALLOWED:", allowed)

        print("🔥 ============================\n")

        return allowed