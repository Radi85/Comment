from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, permissions
from comment.models import Comment
from comment.api.serializers import (
    CommentSerializer,
    create_comment_serializer,
)
from comment.api.permissions import IsOwnerOrReadOnly, QuerySetPermission


class CommentCreate(generics.CreateAPIView):
    queryset = Comment.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        model_type = self.request.GET.get("type")
        pk = self.request.GET.get("id")
        parent_id = self.request.GET.get("parent_id", None)
        return create_comment_serializer(
                model_type=model_type,
                pk=pk,
                parent_id=parent_id,
                user=self.request.user
                )


class CommentList(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
        QuerySetPermission
    )

    def get_queryset(self):
        '''
        Parameters are already validated in the QuerySetPermission
        '''
        model_type = self.request.GET.get("type")
        pk = self.request.GET.get("id")
        content_type_model = ContentType.objects.get(model=model_type.lower())
        Model = content_type_model.model_class()
        model_obj = Model.objects.filter(id=pk).first()
        return Comment.objects.filter_by_object(model_obj)


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)
