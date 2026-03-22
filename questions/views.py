from django.shortcuts import render

def index(request):
    return render(request, 'questions/index.html')

def question(request, question_id):
    return render(request, 'questions/question.html')

def ask(request):
    return render(request, 'questions/ask.html')

def tag(request, tag_name):
    return render(request, 'questions/tag.html')
