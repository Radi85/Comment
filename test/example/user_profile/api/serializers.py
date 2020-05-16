from django.contrib.auth.models import User
from rest_framework import serializers

from user_profile.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('display_name', 'image', 'birth_date')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail', lookup_field='username')

    post_set = serializers.HyperlinkedRelatedField(view_name='post-detail', read_only=True, many=True)
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = (
            'url',
            'id',
            'username',
            'first_name',
            'last_name',
            'post_set',
            'profile'
        )

        lookup_field = 'username'
