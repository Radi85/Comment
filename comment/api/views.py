from django.contrib.contenttypes.models import ContentType

from rest_framework import generics, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from comment.api.serializers import CommentSerializer, CommentCreateSerializer
from comment.api.permissions import IsOwnerOrReadOnly, ContentTypePermission, ParentIdPermission
from comment.models import Comment, ReactionInstance


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


class CommentDetailForReaction(generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @staticmethod
    def _clean_reaction(reaction):
        if (not isinstance(reaction, str)) or (not getattr(ReactionInstance.ReactionType, reaction.upper(), None)):
            return None
        return reaction.lower()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['reaction_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        reaction = kwargs.get('reaction', None)
        reaction_type = self._clean_reaction(reaction)
        if not reaction_type:
            data = {'error': 'This is an invalid reaction type'}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        ReactionInstance.objects.set_reaction(
            user=request.user,
            reaction=comment.reaction,
            reaction_type=reaction_type
        )
        comment.reaction.refresh_from_db()
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)
