from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('profile/', include('test.example.profile.urls')),
    path('admin/', admin.site.urls, name='admin'),
    path('comment/', include('comment.urls')),
    path('api/', include('comment.api.urls')),
]
