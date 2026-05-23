from django.core.cache import cache
from django.conf import settings


def sidebar_data(request):
    popular_tags = cache.get('popular_tags_cache')
    if not popular_tags:
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        from questions.models import Tag

        three_months_ago = timezone.now() - timedelta(days=90)
        popular_tags = list(
            Tag.objects
            .filter(questions__created_at__gte=three_months_ago)
            .annotate(questions_count=Count('questions', distinct=True))
            .order_by('-questions_count')[:20]
        )
        cache.set('popular_tags_cache', popular_tags, 60 * 10)

    best_users = cache.get('best_users_cache')
    if not best_users:
        from django.db.models import Q, Sum, Value, IntegerField
        from django.db.models.functions import Coalesce
        from django.contrib.auth.models import User
        from django.utils import timezone
        from datetime import timedelta

        week_ago = timezone.now() - timedelta(days=7)
        best_users = list(
            User.objects
            .annotate(
                weekly_score=(
                    Coalesce(
                        Sum('questions__rating', filter=Q(questions__created_at__gte=week_ago)),
                        Value(0, output_field=IntegerField()),
                    ) +
                    Coalesce(
                        Sum('answers__rating', filter=Q(answers__created_at__gte=week_ago)),
                        Value(0, output_field=IntegerField()),
                    )
                )
            )
            .order_by('-weekly_score')[:10]
        )
        cache.set('best_users_cache', best_users, 60 * 10)

    return {
        'popular_tags': popular_tags,
        'best_users': best_users,
    }


def media_settings(request):
    return {
        'MEDIA_URL': settings.MEDIA_URL,
        'DEFAULT_AVATAR_URL': settings.DEFAULT_AVATAR_URL,
    }
