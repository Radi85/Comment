from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from comment.api.serializers import CommentSerializer, CommentCreateSerializer
from comment.api.permissions import (
    IsOwnerOrReadOnly, ContentTypePermission, ParentIdPermission, FlagEnabledPermission, CanChangeFlaggedCommentState
)
from comment.models import Comment, Reaction, ReactionInstance, Flag, FlagInstance


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['reaction_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        reaction_type = kwargs.get('reaction', None)
        reaction_obj = Reaction.objects.get_reaction_object(comment)
        try:
            ReactionInstance.objects.set_reaction(
                user=request.user,
                reaction=reaction_obj,
                reaction_type=reaction_type
            )
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        comment.reaction.refresh_from_db()
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentDetailForFlag(generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, FlagEnabledPermission)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['flag_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        flag = Flag.objects.get_for_comment(comment)
        reason = request.data.get('reason') or request.POST.get('reason')
        info = request.data.get('info') or request.POST.get('info')
        try:
            FlagInstance.objects.set_flag(request.user, flag, reason=reason, info=info)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentDetailForFlagStateChange(generics.RetrieveAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (CanChangeFlaggedCommentState, )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['flag_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        flag = Flag.objects.get_for_comment(comment)
        if not comment.is_flagged:
            raise PermissionDenied(detail='You do not have permission to perform this action.')
        state = request.data.get('state') or request.POST.get('state')
        try:
            state = flag.get_clean_state(state)
            if not comment.is_edited and state == flag.RESOLVED:
                return Response(
                    {'error': 'The comment must be edited before resolving the flag'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            flag.toggle_state(state, request.user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)
