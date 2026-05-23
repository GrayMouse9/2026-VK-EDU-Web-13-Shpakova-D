from django.contrib import admin
from .models import Tag, Question, Answer, QuestionLike, AnswerLike


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ('author',)
    fields = ('author', 'text', 'is_correct', 'rating', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'rating', 'created_at')
    list_filter = ('created_at', 'tags')
    search_fields = ('title', 'text')
    raw_id_fields = ('author',)
    filter_horizontal = ('tags',)
    inlines = [AnswerInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related('tags')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'rating', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('text',)
    raw_id_fields = ('author', 'question')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'question')


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'value')
    list_filter = ('value',)
    raw_id_fields = ('user', 'question')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'answer', 'value')
    list_filter = ('value',)
    raw_id_fields = ('user', 'answer')
