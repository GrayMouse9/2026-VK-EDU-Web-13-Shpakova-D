from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Count
from questions.models import Tag
from django.conf import settings

def sidebar_data(request):
    popular_tags = cache.get('popular_tags_cache')

    if not popular_tags:
        popular_tags = list(
            Tag.objects
            .annotate(questions_count=Count('questions', distinct=True))
            .order_by('-questions_count')[:20]
        )
        cache.set('popular_tags_cache', popular_tags, 900)

    best_users = cache.get('best_users_cache')

    if not best_users:
        best_users = list(
            User.objects
            .annotate(
                activity=Count('questions', distinct=True) + Count('answers', distinct=True)
            )
            .order_by('-activity')[:10]
        )
        cache.set('best_users_cache', best_users, 900)

    return {
        'popular_tags': popular_tags,
        'best_users': best_users,
    }

def media_settings(request):
    """Прокидываем MEDIA_URL и дефолтную аватарку в каждый шаблон."""
    return {
        'MEDIA_URL': settings.MEDIA_URL,
        'DEFAULT_AVATAR_URL': settings.DEFAULT_AVATAR_URL,
    }
