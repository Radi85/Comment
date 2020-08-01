from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def set_default_email(apps, schema_editor):
    comment_model = apps.get_model('comment', 'Comment')
    for comment in comment_model.objects.all():
        comment.email = comment.user.email
        comment.save(update_fields=['email'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('comment', '0008_comment_urlhash'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='email',
            field=models.EmailField(default=None, max_length=254, null=True),
        ),
        migrations.RunPython(set_default_email, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='comment',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='posted',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
