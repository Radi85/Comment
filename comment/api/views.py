from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, permissions
from comment.models import Comment
from comment.api.serializers import CommentSerializer, CommentCreateSerializer

from comment.api.permissions import IsOwnerOrReadOnly, ContentTypePermission, ParentIdPermission


class CommentCreate(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = (permissions.IsAuthenticated, ContentTypePermission, ParentIdPermission)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        context['model_type'] = self.request.GET.get("type")
        context['model_id'] = self.request.GET.get("id")
        context['parent_id'] = self.request.GET.get("parent_id")
        return context


class CommentList(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, ContentTypePermission)

    def get_queryset(self):
        model_type = self.request.GET.get("type")
        pk = self.request.GET.get("id")
        content_type_model = ContentType.objects.get(model=model_type.lower())
        model_class = content_type_model.model_class()
        model_obj = model_class.objects.filter(id=pk).first()
        return Comment.objects.filter_parents_by_object(model_obj)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
