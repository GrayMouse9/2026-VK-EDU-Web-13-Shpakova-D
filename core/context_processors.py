from django.contrib.auth.models import User
from django.db.models import Count
from questions.models import Tag


def sidebar_data(request):
    """Подгружает данные для общего сайдбара: популярные теги и активные пользователи."""

    popular_tags = (
        Tag.objects
        .annotate(questions_count=Count('questions', distinct=True))
        .order_by('-questions_count')[:20]
    )

    best_users = (
        User.objects
        .annotate(
            activity=Count('questions', distinct=True) + Count('answers', distinct=True)
        )
        .order_by('-activity')[:10]
    )

    return {
        'popular_tags': popular_tags,
        'best_users': best_users,
    }
