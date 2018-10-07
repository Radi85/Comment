from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owner of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # GET, HEAD or OPTIONS requests are SAFE_METHODS.
        if request.method in permissions.SAFE_METHODS:
            return True

        # PUT and DELETE permissions are only allowed to the author of the blog.
        return obj.user == request.user
