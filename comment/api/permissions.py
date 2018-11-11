from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
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


class QuerySetPermission(permissions.BasePermission):
    message = ""

    def has_permission(self, request, view):
        model_type = request.GET.get("type")
        slug = request.GET.get("slug", None)
        pk = request.GET.get("id", None)
        try:
            model = ContentType.objects.get(model=model_type.lower()).model_class()
            model_obj = model.objects.filter(Q(id=pk)|Q(slug=slug))
            if not model_obj.exists() and model_obj.count() != 1:
                self.message = "this is not a valid id or slug for this model"
                return False
            return True
        except ContentType.DoesNotExist:
            self.message = "this is not a valid content type."
            return False
