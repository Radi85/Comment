from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from comment.models import Comment
from comment.api.serializers import (
    CommentSerializer,
    CommentDetailSerializer,
    create_comment_serializer,
)
from comment.api.permissions import IsOwnerOrReadOnly


class CommentCreate(generics.CreateAPIView):
    queryset = Comment.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        model_type = self.request.GET.get("type")
        slug = self.request.GET.get("slug", None)
        pk = self.request.GET.get("id", None)
        parent_id = self.request.GET.get("parent_id", None)
        return create_comment_serializer(
                model_type=model_type,
                pk=pk,
                slug=slug,
                parent_id=parent_id,
                user=self.request.user
                )


class CommentList(generics.ListAPIView):
    queryset = Comment.objects.all_parent_comments()
    serializer_class = CommentSerializer


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)
