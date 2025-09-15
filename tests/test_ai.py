from dataclasses import dataclass

import pytest

from visual_novel_chat.ai import AiResponder, EmotionClassifier
from visual_novel_chat.database import ConversationHistory


def test_emotion_classifier_uses_pipeline_factory():
    calls = []

    def pipeline_factory():
        def pipeline_fn(text, truncation, max_length):
            calls.append((text, truncation, max_length))
            return [[{"label": "joy", "score": 0.9}]]

        return pipeline_fn

    classifier = EmotionClassifier(pipeline_factory=pipeline_factory)
    prediction = classifier.predict("hello there")

    assert prediction["label"] == "joy"
    assert pytest.approx(prediction["score"]) == 0.9
    assert calls == [("hello there", True, 512)]


@dataclass
class DummyResponse:
    message: object


@dataclass
class DummyMessage:
    content: str


def test_ai_responder_persists_conversation(tmp_path):
    db_path = tmp_path / "history.db"
    history = ConversationHistory(db_path)

    def fake_chat(model, messages):
        assert model == "llama3.2"
        assert messages[0]["role"] == "system"
        return DummyResponse(message=DummyMessage(content="response text"))

    responder = AiResponder(history=history, chat_callable=fake_chat)
    config = {"SYSTEM_PROMPT": "system"}
    reply = responder.query("question", user_id="user", user_name="name", config=config)

    assert reply == "response text"
    conversation = history.get_conversation("user")
    assert conversation[0].role == "system"
    assert conversation[-1].role == "assistant"
