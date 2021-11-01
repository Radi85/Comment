from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.models import signals
from django.core.checks import register, Tags


class CommentConfig(AppConfig):
    name = 'comment'
    verbose_name = _('comment')

    def ready(self):
        import comment.signals
        import comment.checks

        signals.post_migrate.connect(comment.signals.create_permission_groups, sender=self)
        signals.post_migrate.connect(comment.signals.adjust_flagged_comments, sender=self)

        register(comment.checks.check_orders_unique, Tags.compatibility)
        register(comment.checks.check_order_values, Tags.compatibility)
