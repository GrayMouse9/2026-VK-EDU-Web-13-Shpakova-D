from celery import shared_task
from django.conf import settings
from cent import Client
from requests import Session


@shared_task
def publish_new_answer(question_id, answer_data):
    try:
        session = Session()
        session.trust_env = False
        client = Client(
            settings.CENTRIFUGO_API_URL,
            api_key=settings.CENTRIFUGO_API_KEY,
            timeout=2,
            session=session,
        )
        client.publish(f'questions:{question_id}', answer_data)
    except Exception:
        pass


@shared_task
def notify_new_answer(question_title, answer_author, answer_url, recipient_email):
    if not recipient_email:
        return
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    send_mail(
        subject=f'Новый ответ на вопрос «{question_title}»',
        message=(
            f'Пользователь {answer_author} ответил на ваш вопрос.\n\n'
            f'Перейти к ответу: {answer_url}'
        ),
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=True,
    )


@shared_task
def recalculate_popular_tags():
    from django.core.cache import cache
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


@shared_task
def recalculate_best_members():
    from django.core.cache import cache
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
