from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse_lazy

from .models import Question, Tag
from .forms import AskForm, AnswerForm

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
            return redirect(f"{request.path}#answer-{answer.id}")
    else:
        form = AnswerForm()

    answers = item.answers.all().select_related('author')
    page = paginate(answers, request, per_page=30)
    return render(request, 'questions/question.html', {
        'question': item,
        'page': page,
        'form': form,
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

@require_POST
def vote_question(request, question_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    action = request.POST.get('action')
    value = 1 if action == 'up' else -1
    question = get_object_or_404(Question, pk=question_id)

    like, created = QuestionLike.objects.get_or_create(
        user=request.user, question=question, defaults={'value': value}
    )

    user_vote = 0

    if not created:
        if like.value == value:
            like.delete()
            question.rating -= value
            user_vote = 0
        else:
            question.rating += (value * 2)
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
        return JsonResponse({'error': 'Login required'}, status=401)

    action = request.POST.get('action')
    value = 1 if action == 'up' else -1
    answer = get_object_or_404(Answer, pk=answer_id)

    like, created = AnswerLike.objects.get_or_create(
        user=request.user, answer=answer, defaults={'value': value}
    )

    user_vote = 0

    if not created:
        if like.value == value:
            like.delete()
            answer.rating -= value
            user_vote = 0
        else:
            answer.rating += (value * 2)
            like.value = value
            like.save()
            user_vote = value
    else:
        answer.rating += value
        user_vote = value

    answer.save()
    return JsonResponse({'rating': answer.rating, 'user_vote': user_vote})
