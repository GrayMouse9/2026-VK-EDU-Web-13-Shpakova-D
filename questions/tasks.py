from django.conf import settings
from cent import Client, PublishRequest
from requests import Session


def publish_new_answer(question_id, answer_data):
    try:
        session = Session()
        session.trust_env = False
        client = Client(
            settings.CENTRIFUGO_API_URL,
            api_key=settings.CENTRIFUGO_API_KEY,
            timeout=2,
            session=session,
        )
        client.publish(PublishRequest(
            channel=f'questions:{question_id}',
            data=answer_data,
        ))
    except Exception:
        pass
