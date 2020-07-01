from django.db import migrations, models

from comment.utils import id_generator


def generate_urlhash():
    return id_generator(
        prefix='comment',
        len_id=8,
        suffix=''
        )


def set_unique_urlhash(model, instance):
    if not instance.urlhash:
        instance.urlhash = generate_urlhash()
        while model.objects.filter(urlhash=instance.urlhash).exists():
            instance.urlhash = generate_urlhash()


def set_default_urlhash(apps, schema_editor):
    comment_model = apps.get_model('comment', 'Comment')
    for comment in comment_model.objects.all():
        set_unique_urlhash(comment_model, comment)
        comment.save(update_fields=['urlhash'])


class Migration(migrations.Migration):

    dependencies = [
        ('comment', '0007_auto_20200620_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='urlhash',
            field=models.CharField(null=True, default=None, editable=False, max_length=50),
        ),
        migrations.RunPython(set_default_urlhash, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='comment',
            name='urlhash',
            field=models.CharField(editable=False, max_length=50, unique=True)
        )
    ]
