from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

QUESTIONS = [
    {
        'id': i,
        'title': f'Как правильно отцентровать div?',
        'text': f'Текст вопроса {i}. Уже третий день пытаюсь выровнять блок по центру экрана. Пробовал использовать margin: 0 auto, но по вертикали он не выравнивается. Помогите разобраться с Flexbox!',
        'answers_count': i % 5,
        'tags': ['css', 'html'],
        'author': 'Dr. Pepper',
        'rating': i * 2,
    } for i in range(1, 40)
]

ANSWERS = [
    {
        'id': i,
        'text': f'Чтобы выровнять div по центру с помощью Flexbox, нужно задать родителю display: flex, а затем использовать justify-content: center и align-items: center.',
        'author': f'User {i}',
        'rating': i * 3,
        'is_correct': i == 1,
        } for i in range(1, 30)
]

def question(request, question_id):
    item = next((q for q in QUESTIONS if q['id'] == int(question_id)), None)

    page = paginate(ANSWERS, request, per_page=5)

    return render(request, 'questions/question.html', {'question': item, 'page': page})

def paginate(objects_list, request, per_page=10):
    """Вспомогательная функция для пагинации"""
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page.custom_page_range = paginator.get_elided_page_range(page.number, on_each_side=2, on_ends=1)

    return page

def index(request):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'questions/index.html', {'page': page})

def ask(request):
    return render(request, 'questions/ask.html')

def tag(request, tag_name):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag_name})
def hot(request):
    hot_questions = sorted(QUESTIONS, key=lambda x: x['rating'], reverse=True)
    page = paginate(hot_questions, request, per_page=5)
    return render(request, 'questions/hot.html', {'page': page})
