from django import forms
from .models import Question, Answer, Tag


class AskForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'python, django, sql'}),
        help_text='Введите до 3 тегов через запятую.',
    )

    text = forms.CharField(
        label='Текст',
        max_length=10000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок вопроса'}),
        }
        labels = {
            'title': 'Заголовок',
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
    text = forms.CharField(
        label='Текст ответа',
        max_length=10000,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Напишите ваш ответ...'})
    )

    class Meta:
        model = Answer
        fields = ('text',)
    def save(self, commit=True, author=None, question=None):
        answer = super().save(commit=False)
        if author:
            answer.author = author
        if question:
            answer.question = question
        if commit:
            answer.save()
        return answer
