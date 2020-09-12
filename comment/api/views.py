from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from comment.validators import ValidatorMixin, ContentTypeValidator
from comment.api.serializers import CommentSerializer, CommentCreateSerializer
from comment.api.permissions import (
    IsOwnerOrReadOnly, FlagEnabledPermission, CanChangeFlaggedCommentState
)
from comment.models import Comment, Reaction, ReactionInstance, Flag, FlagInstance
from comment.utils import get_comment_from_key, CommentFailReason


class CommentCreate(ValidatorMixin, generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = ()
    api = True

    def get_serializer_context(self):
        self.validate(self.request)
        context = super().get_serializer_context()
        context['user'] = self.request.user
        context['model_name'] = self.model_name
        context['app_name'] = self.app_name
        context['model_id'] = self.model_id
        context['parent_id'] = self.parent_id
        context['email'] = self.request.GET.get('email', None)
        return context


class CommentList(ContentTypeValidator, generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    api = True

    def get_queryset(self):
        self.validate(self.request)
        model_name = self.model_name
        pk = self.model_id
        content_type_model = ContentType.objects.get(model=model_name.lower())
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
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response(
                {'detail': _('This action cannot be applied on unflagged comments')},
                status=status.HTTP_400_BAD_REQUEST
            )
        state = request.data.get('state') or request.POST.get('state')
        try:
            state = flag.get_clean_state(state)
            if not comment.is_edited and state == flag.RESOLVED:
                return Response(
                    {'detail': _('The comment must be edited before resolving the flag')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            flag.toggle_state(state, request.user)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConfirmComment(APIView):
    def get(self, request, *args, **kwargs):
        key = kwargs.get('key', None)
        comment = get_comment_from_key(key)

        if comment.why_invalid == CommentFailReason.BAD:
            return Response({'detail': _('Bad Signature, Comment discarded')}, status=status.HTTP_400_BAD_REQUEST)

        if comment.why_invalid == CommentFailReason.EXISTS:
            return Response({'detail': _('Comment already verified')}, status=status.HTTP_200_OK)

        return Response(CommentSerializer(comment.obj).data, status=status.HTTP_201_CREATED)
