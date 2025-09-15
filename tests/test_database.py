from visual_novel_chat.database import ConversationHistory


def test_conversation_history_roundtrip(tmp_path):
    db_path = tmp_path / "history.db"
    history = ConversationHistory(db_path)
    history.add_message("user", "system", "hello")
    history.add_message("user", "user", "Hi")
    history.add_message("user", "assistant", "Hello there")

    messages = history.get_conversation("user")
    assert [m.role for m in messages] == ["system", "user", "assistant"]
    assert [m.content for m in messages][-1] == "Hello there"


def test_conversation_history_prunes_old_messages(tmp_path):
    db_path = tmp_path / "history.db"
    history = ConversationHistory(db_path)
    history.add_message("user", "system", "hello")
    for i in range(10):
        history.add_message("user", "user", f"question-{i}")
    history.prune_conversation("user", max_messages=5)

    messages = history.get_conversation("user")
    assert messages[0].role == "system"
    assert len(messages) == 5
    assert messages[-1].content == "question-9"
