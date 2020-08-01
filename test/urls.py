from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('profile/', include('test.example.user_profile.urls')),
    path('admin/', admin.site.urls, name='admin'),
    path('comment/', include('comment.urls')),
    path('api/', include('comment.api.urls')),
    path('post/', include('test.example.post.urls'))
]
