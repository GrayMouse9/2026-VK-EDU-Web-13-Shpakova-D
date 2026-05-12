from django import forms
from .models import Question, Answer, Tag


class AskForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'python, django, sql'}),
        help_text='Введите до 3 тегов через запятую.',
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок вопроса'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'title': 'Заголовок',
            'text': 'Текст',
        }

    def clean_tags(self):
        raw = self.cleaned_data.get('tags', '')
        names = [t.strip() for t in raw.split(',') if t.strip()]
        if len(names) > 3:
            raise forms.ValidationError('Максимум 3 тега')
        return names

    def save(self, commit=True, author=None):
        question = super().save(commit=False)
        if author:
            question.author = author
        if commit:
            question.save()
            tag_names = self.cleaned_data.get('tags', [])
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                question.tags.add(tag)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Напишите ваш ответ...'}),
        }
        labels = {
            'text': 'Текст ответа',
        }

    def save(self, commit=True, author=None, question=None):
        answer = super().save(commit=False)
        if author:
            answer.author = author
        if question:
            answer.question = question
        if commit:
            answer.save()
        return answer

class VoteForm(forms.Form):
    ACTION_UP = 'up'
    ACTION_DOWN = 'down'
    ACTION_CHOICES = [(ACTION_UP, 'up'), (ACTION_DOWN, 'down')]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        error_messages={
            'required': 'Параметр "action" обязателен.',
            'invalid_choice': 'Допустимые значения action: "up" или "down".',
        },
    )

    @property
    def value(self):
        return 1 if self.cleaned_data['action'] == self.ACTION_UP else -1

class MarkCorrectForm(forms.Form):
    """Валидация входных данных AJAX-отметки правильного ответа."""

    answer_id = forms.IntegerField(
        min_value=1,
        error_messages={
            'required': 'Параметр answer_id обязателен.',
            'invalid': 'answer_id должен быть числом.',
            'min_value': 'answer_id должен быть положительным.',
        },
    )

    def __init__(self, *args, question=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question

    def clean_answer_id(self):
        answer_id = self.cleaned_data['answer_id']
        if self.question is None:
            raise forms.ValidationError('Вопрос не передан в форму.')
        try:
            self.answer = Answer.objects.get(pk=answer_id, question=self.question)
        except Answer.DoesNotExist:
            raise forms.ValidationError('Ответ не найден для этого вопроса.')
        return answer_id
