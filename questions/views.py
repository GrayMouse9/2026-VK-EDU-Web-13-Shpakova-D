import time
import jwt

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse, reverse_lazy
from django.db import transaction

from .models import Question, Tag
from .forms import AskForm, AnswerForm, VoteForm, MarkCorrectForm
from .tasks import publish_new_answer, notify_new_answer

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import QuestionLike, AnswerLike, Answer


def paginate(objects_list, request, per_page=20):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    page.custom_page_range = paginator.get_elided_page_range(
        page.number, on_each_side=2, on_ends=1
    )
    return page


def index(request):
    page = paginate(Question.objects.new(), request, per_page=20)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    page = paginate(Question.objects.hot(), request, per_page=20)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    get_object_or_404(Tag, name=tag_name)
    page = paginate(Question.objects.by_tag(tag_name), request, per_page=20)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag_name})


def search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    vector = SearchVector('title', weight='A') + SearchVector('text', weight='B')
    query = SearchQuery(q)
    results = (
        Question.objects
        .annotate(rank=SearchRank(vector, query))
        .filter(rank__gt=0)
        .order_by('-rank')[:8]
    )
    data = [
        {'id': item.id, 'title': item.title, 'url': reverse('question', args=[item.id])}
        for item in results
    ]
    return JsonResponse(data, safe=False)


def question(request, question_id):
    item = get_object_or_404(
        Question.objects.select_related('author').prefetch_related('tags'),
        pk=question_id,
    )

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse_lazy('login')}?next={request.path}")
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(author=request.user, question=item)
            publish_new_answer.delay(item.id, {
                'id': answer.id,
                'text': answer.text,
                'author': answer.author.username,
                'created_at': answer.created_at.strftime('%d.%m.%Y'),
                'rating': answer.rating,
                'is_correct': answer.is_correct,
            })
            notify_new_answer.delay(
                question_title=item.title,
                answer_author=answer.author.username,
                answer_url=request.build_absolute_uri(f"{request.path}#answer-{answer.id}"),
                recipient_email=item.author.email,
            )
            return redirect(f"{request.path}#answer-{answer.id}")
    else:
        form = AnswerForm()

    answers = item.answers.all().select_related('author')
    page = paginate(answers, request, per_page=30)
    return render(request, 'questions/question.html', {
        'question': item,
        'page': page,
        'form': form,
        'centrifugo_ws_url': settings.CENTRIFUGO_WS_URL,
    })


@login_required(login_url=reverse_lazy('login'))
def ask(request):
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            question = form.save(author=request.user)
            return redirect('question', question_id=question.id)
    else:
        form = AskForm()
    return render(request, 'questions/ask.html', {'form': form})

@login_required(login_url=reverse_lazy('login'))
def centrifugo_token(request):
    payload = {
        'sub': str(request.user.id),
        'exp': int(time.time()) + 3600,
    }
    token = jwt.encode(payload, settings.CENTRIFUGO_TOKEN_SECRET, algorithm='HS256')
    return JsonResponse({'token': token})


def _vote_invalid(form):
    return JsonResponse(
        {'error': 'Невалидные параметры запроса.', 'details': form.errors},
        status=400,
    )


def _vote_unauth():
    return JsonResponse(
        {'error': 'Требуется авторизация.', 'login_url': reverse('login')},
        status=401,
    )


@require_POST
def vote_question(request, question_id):
    if not request.user.is_authenticated:
        return _vote_unauth()

    form = VoteForm(request.POST)
    if not form.is_valid():
        return _vote_invalid(form)

    value = form.value

    with transaction.atomic():
        question = get_object_or_404(
            Question.objects.select_for_update(), pk=question_id
        )
        like, created = QuestionLike.objects.get_or_create(
            user=request.user, question=question, defaults={'value': value}
        )
        if not created:
            if like.value == value:
                like.delete()
                question.rating -= value
                user_vote = 0
            else:
                question.rating += value * 2
                like.value = value
                like.save()
                user_vote = value
        else:
            question.rating += value
            user_vote = value
        question.save()

    return JsonResponse({'rating': question.rating, 'user_vote': user_vote})


@require_POST
def vote_answer(request, answer_id):
    if not request.user.is_authenticated:
        return _vote_unauth()

    form = VoteForm(request.POST)
    if not form.is_valid():
        return _vote_invalid(form)

    value = form.value

    with transaction.atomic():
        answer = get_object_or_404(
            Answer.objects.select_for_update(), pk=answer_id
        )
        like, created = AnswerLike.objects.get_or_create(
            user=request.user, answer=answer, defaults={'value': value}
        )
        if not created:
            if like.value == value:
                like.delete()
                answer.rating -= value
                user_vote = 0
            else:
                answer.rating += value * 2
                like.value = value
                like.save()
                user_vote = value
        else:
            answer.rating += value
            user_vote = value
        answer.save()

    return JsonResponse({'rating': answer.rating, 'user_vote': user_vote})

@require_POST
def mark_correct(request, question_id):
    if not request.user.is_authenticated:
        return _vote_unauth()

    question = get_object_or_404(Question, pk=question_id)

    if question.author_id != request.user.id:
        return JsonResponse(
            {'error': 'Только автор вопроса может отмечать правильный ответ.'},
            status=403,
        )

    form = MarkCorrectForm(request.POST, question=question)
    if not form.is_valid():
        return _vote_invalid(form)

    answer = form.answer

    with transaction.atomic():
        answer = Answer.objects.select_for_update().get(pk=answer.pk)
        was_correct = answer.is_correct

        Answer.objects.filter(question=question).exclude(pk=answer.pk).update(is_correct=False)

        answer.is_correct = not was_correct
        answer.save(update_fields=['is_correct'])

    return JsonResponse({
        'answer_id': answer.id,
        'question_id': question.id,
        'is_correct': answer.is_correct,
    })
