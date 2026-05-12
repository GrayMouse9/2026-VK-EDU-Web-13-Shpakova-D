import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker

from core.models import Profile
from questions.models import Question, Answer, Tag, QuestionLike, AnswerLike


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными. Аргумент: ratio."

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Коэффициент заполнения')

    def handle(self, *args, **options):
        ratio = options['ratio']
        fake = Faker('ru_RU')

        # 1. Пользователи
        self.stdout.write(f"Создаю {ratio} пользователей...")
        users = User.objects.bulk_create([
            User(
                username=f"{fake.user_name()}_{i}",
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            for i in range(ratio)
        ], batch_size=1000)
        user_ids = [u.pk for u in users]

        # 1b. Профили (1:1 к пользователю)
        Profile.objects.bulk_create(
            [Profile(user_id=uid) for uid in user_ids],
            batch_size=1000,
        )

        # 2. Теги
        self.stdout.write(f"Создаю {ratio} тегов...")
        tags = Tag.objects.bulk_create([
            Tag(name=f"{fake.word()}_{i}")
            for i in range(ratio)
        ], batch_size=1000)
        tag_ids = [t.pk for t in tags]

        # 3. Вопросы (ratio * 10)
        questions_count = ratio * 10
        self.stdout.write(f"Создаю {questions_count} вопросов...")
        questions = Question.objects.bulk_create([
            Question(
                title=fake.sentence(nb_words=6)[:255],
                text=fake.text(max_nb_chars=500),
                author_id=random.choice(user_ids),
                rating=random.randint(0, 100),
            )
            for _ in range(questions_count)
        ], batch_size=1000)
        question_ids = [q.pk for q in questions]

        # 3b. Связи вопрос ↔ тег (M2M через through-модель)
        self.stdout.write("Привязываю теги к вопросам...")
        ThroughModel = Question.tags.through
        through_objs = [
            ThroughModel(question_id=qid, tag_id=tid)
            for qid in question_ids
            for tid in random.sample(tag_ids, k=min(3, len(tag_ids)))
        ]
        ThroughModel.objects.bulk_create(
            through_objs, batch_size=10000, ignore_conflicts=True
        )

        # 4. Ответы (ratio * 100)
        answers_count = ratio * 100
        self.stdout.write(f"Создаю {answers_count} ответов...")
        answers = Answer.objects.bulk_create([
            Answer(
                text=fake.text(max_nb_chars=300),
                question_id=random.choice(question_ids),
                author_id=random.choice(user_ids),
                is_correct=random.random() < 0.1,
                rating=random.randint(0, 50),
            )
            for _ in range(answers_count)
        ], batch_size=1000)
        answer_ids = [a.pk for a in answers]

        # 5. Лайки на вопросы (ratio * 100)
        target_q_likes = min(ratio * 100, len(user_ids) * len(question_ids))
        self.stdout.write(f"Создаю {target_q_likes} лайков на вопросы...")
        seen_q = set()
        q_likes_data = []
        while len(q_likes_data) < target_q_likes:
            uid = random.choice(user_ids)
            qid = random.choice(question_ids)
            if (uid, qid) in seen_q:
                continue
            seen_q.add((uid, qid))
            q_likes_data.append(QuestionLike(
                user_id=uid, question_id=qid, value=random.choice([1, -1])
            ))
        QuestionLike.objects.bulk_create(
            q_likes_data, batch_size=10000, ignore_conflicts=True
        )

        # 5b. Лайки на ответы (ratio * 100)
        target_a_likes = min(ratio * 100, len(user_ids) * len(answer_ids))
        self.stdout.write(f"Создаю {target_a_likes} лайков на ответы...")
        seen_a = set()
        a_likes_data = []
        while len(a_likes_data) < target_a_likes:
            uid = random.choice(user_ids)
            aid = random.choice(answer_ids)
            if (uid, aid) in seen_a:
                continue
            seen_a.add((uid, aid))
            a_likes_data.append(AnswerLike(
                user_id=uid, answer_id=aid, value=random.choice([1, -1])
            ))
        AnswerLike.objects.bulk_create(
            a_likes_data, batch_size=10000, ignore_conflicts=True
        )

        self.stdout.write(self.style.SUCCESS("Готово!"))
