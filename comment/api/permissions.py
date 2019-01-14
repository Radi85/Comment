from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owner of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # GET, HEAD or OPTIONS requests are SAFE_METHODS.
        if request.method in permissions.SAFE_METHODS:
            return True
        # PUT and DELETE permissions are allowed to the owner of the comment.
        return obj.user == request.user


class QuerySetPermission(permissions.BasePermission):
    message = ""

    def has_permission(self, request, view):
        model_type = request.GET.get("type")
        pk = request.GET.get("id")
        try:
            model_type = model_type.lower()
            ct = ContentType.objects.get(model=model_type).model_class()
            Model = ct.objects.filter(id=pk)
            if not Model.exists() and Model.count() != 1:
                self.message = "this is not a valid id for this model"
                return False
            return True
        except ContentType.DoesNotExist:
            self.message = "this is not a valid content type."
            return False
        except AttributeError:
            msg = "content type must be specified to retrieve comment list"
            self.message = msg
            return False
        except ValueError:
            self.message = "the id must be an integer"
