from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class QuestionManager(models.Manager):
    def with_related(self):
        return (
            self.get_queryset()
            .select_related('author')
            .prefetch_related('tags')
            .annotate(answers_count=Count('answers'))
        )

    def new(self):
        return self.with_related().order_by('-created_at')

    def hot(self):
        return self.with_related().order_by('-rating')

    def by_tag(self, tag_name):
        return self.with_related().filter(tags__name=tag_name).order_by('-rating')

class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions', verbose_name='Автор')
    tags = models.ManyToManyField(Tag, blank=True, related_name='questions', verbose_name='Теги')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    objects = QuestionManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Answer(models.Model):
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers', verbose_name='Автор')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Ответ на "{self.question.title}" от {self.author.username}'

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'


class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_likes', verbose_name='Пользователь')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='likes', verbose_name='Вопрос')
    value = models.SmallIntegerField(default=1, verbose_name='Значение')  # 1 или -1

    class Meta:
        unique_together = ('user', 'question')
        verbose_name = 'Лайк вопроса'
        verbose_name_plural = 'Лайки вопросов'


class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answer_likes', verbose_name='Пользователь')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='likes', verbose_name='Ответ')
    value = models.SmallIntegerField(default=1, verbose_name='Значение')  # 1 или -1

    class Meta:
        unique_together = ('user', 'answer')
        verbose_name = 'Лайк ответа'
        verbose_name_plural = 'Лайки ответов'
