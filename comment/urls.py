from django.urls import path
from comment.views import CreateComment, UpdateComment, DeleteComment


app_name = 'comment'

urlpatterns = [
    path('create/', CreateComment.as_view(), name='create'),
    path('edit/<int:pk>/', UpdateComment.as_view(), name='edit'),
    path('delete/<int:pk>/', DeleteComment.as_view(), name='delete'),
]
