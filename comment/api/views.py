from django.core.exceptions import ValidationError
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from comment.validators import ValidatorMixin, ContentTypeValidator
from comment.api.serializers import CommentSerializer, CommentCreateSerializer
from comment.api.permissions import (
    IsOwnerOrReadOnly, FlagEnabledPermission, CanChangeFlaggedCommentState, SubscriptionEnabled,
    CanGetSubscribers, CanCreatePermission, UserPermittedOrReadOnly, CanBlockUsers
)
from comment.models import Comment, Reaction, ReactionInstance, Flag, FlagInstance, Follower
from comment.utils import get_comment_from_key, CommentFailReason
from comment.messages import FlagError, EmailError
from comment.views import BaseToggleFollowView, CommentCreateMixin, BaseToggleBlockingView


class CommentCreate(ValidatorMixin, generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = (CanCreatePermission, UserPermittedOrReadOnly)
    api = True

    def get_serializer_context(self):
        self.validate(self.request)
        context = super().get_serializer_context()
        context['model_obj'] = self.model_obj
        context['parent_comment'] = self.parent_comment
        context['email'] = self.request.GET.get('email', None)
        return context


class CommentList(ContentTypeValidator, generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    api = True

    def get_queryset(self):
        self.validate(self.request)
        return Comment.objects.filter_parents_by_object(self.model_obj).select_related('user', 'reaction', 'flag')


class CommentDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all().select_related('user', 'reaction', 'flag')
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly, UserPermittedOrReadOnly)


class CommentDetailForReaction(generics.UpdateAPIView):
    queryset = Comment.objects.all().select_related('user', 'reaction', 'flag')
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, UserPermittedOrReadOnly)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['reaction_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
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


class CommentDetailForFlag(generics.UpdateAPIView):
    queryset = Comment.objects.all().select_related('user', 'reaction', 'flag')
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, FlagEnabledPermission, UserPermittedOrReadOnly)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['flag_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        flag = Flag.objects.get_for_comment(comment)
        reason = request.data.get('reason') or request.POST.get('reason')
        info = request.data.get('info') or request.POST.get('info')
        try:
            FlagInstance.objects.set_flag(request.user, flag, reason=reason, info=info)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentDetailForFlagStateChange(generics.UpdateAPIView):
    queryset = Comment.objects.all().select_related('user', 'reaction', 'flag')
    serializer_class = CommentSerializer
    permission_classes = (CanChangeFlaggedCommentState, UserPermittedOrReadOnly)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['flag_update'] = True
        return context

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        flag = Flag.objects.get_for_comment(comment)
        state = request.data.get('state') or request.POST.get('state')
        try:
            state = flag.get_clean_state(state)
            if not comment.is_edited and state == flag.RESOLVED:
                return Response(
                    {'detail': FlagError.RESOLVE_UNEDITED_COMMENT},
                    status=status.HTTP_400_BAD_REQUEST
                )
            flag.toggle_state(state, request.user)
        except ValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConfirmComment(APIView, CommentCreateMixin):
    def get(self, request, *args, **kwargs):
        key = kwargs.get('key', None)
        temp_comment = get_comment_from_key(key)

        if temp_comment.why_invalid == CommentFailReason.BAD:
            return Response({'detail': EmailError.BROKEN_VERIFICATION_LINK}, status=status.HTTP_400_BAD_REQUEST)

        if temp_comment.why_invalid == CommentFailReason.EXISTS:
            return Response({'detail': EmailError.USED_VERIFICATION_LINK}, status=status.HTTP_200_OK)

        comment = self.perform_save(temp_comment.obj, request)

        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class ToggleFollowAPI(BaseToggleFollowView, APIView):
    api = True
    response_class = Response
    permission_classes = (SubscriptionEnabled, permissions.IsAuthenticated, UserPermittedOrReadOnly)

    def post(self, request, *args, **kwargs):
        self.validate(request)
        return super().post(request, *args, **kwargs)


class SubscribersAPI(ContentTypeValidator, APIView):
    api = True
    permission_classes = (CanGetSubscribers,)

    def get(self, request, *args, **kwargs):
        self.validate(request)
        return Response({
            'app_name': self.model_obj._meta.app_label,
            'model_name': self.model_obj.__class__.__name__,
            'model_id': self.model_obj.id,
            'followers': Follower.objects.get_emails_for_model_object(self.model_obj)
        })


class ToggleBlockingAPI(BaseToggleBlockingView, APIView):
    permission_classes = (CanBlockUsers,)
    response_class = Response
