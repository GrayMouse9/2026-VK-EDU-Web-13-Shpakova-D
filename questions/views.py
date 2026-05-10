
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Question, Tag


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
    answers = item.answers.all().select_related('author')
    page = paginate(answers, request, per_page=5)
    return render(request, 'questions/question.html', {'question': item, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
