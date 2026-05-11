from django.db import models
from django.db.models import Count

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
