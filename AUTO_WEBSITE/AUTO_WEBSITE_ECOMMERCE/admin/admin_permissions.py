from rest_framework import permissions

TYPE_1_METHODS = ('GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE')
TYPE_2_METHODS = ('GET', 'OPTIONS', 'HEAD', 'PATCH')
TYPE_3_METHODS = ('GET', 'OPTIONS', 'HEAD', 'PATCH')
TYPE_4_METHODS = ('GET', 'OPTIONS', 'HEAD', 'POST')

class AdminObjectType1Permission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return False

        if request.method in ['POST']:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in TYPE_1_METHODS:
            return True
        return False

class AdminObjectType2Permission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return False

        if request.method in ['POST']:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in TYPE_2_METHODS:
            return True
        return False

class AdminObjectType3Permission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return False

        if request.method in ['POST']:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in TYPE_3_METHODS:
            return True
        return False

class AdminObjectType4Permission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return False

        if request.method in ['POST']:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in TYPE_4_METHODS:
            return True
        return False

class AdminObjectType5Permission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True
        return False

        if request.method in ['POST']:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return False
