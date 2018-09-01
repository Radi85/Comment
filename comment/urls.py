from django.urls import path, re_path
from comment.views import create_comment, edit_comment, delete_comment


app_name = 'comment'

urlpatterns = [
    path('create/', create_comment, name='create'),
    path('edit/<int:pk>', edit_comment, name='edit'),
    path('delete/<int:pk>', delete_comment, name='delete'),
]
