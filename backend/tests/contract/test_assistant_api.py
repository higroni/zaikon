"""Contract tests for assistant endpoints."""

from pathlib import Path


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_assistant_session_answers_with_corpus_citations(client):
    corpus = client.post("/api/v1/corpora", json={"name": "Assistant corpus"}).json()[
        "corpus"
    ]
    client.post(
        f"/api/v1/corpora/{corpus['corpus_id']}/import-folder",
        json={
            "corpus_id": corpus["corpus_id"],
            "folder_uri": str(FIXTURE_DIR / "small_txt_corpus"),
        },
    )
    session_response = client.post(
        "/api/v1/assistant/sessions",
        json={
            "title": "Pitanja o sumama",
            "selected_corpus_id": corpus["corpus_id"],
        },
    )

    assert session_response.status_code == 200
    session = session_response.json()["session"]

    message_response = client.post(
        f"/api/v1/assistant/sessions/{session['session_id']}/messages",
        json={"content_text": "Gde se pominje Ministarstvo i evidencija?", "top_k": 5},
    )

    assert message_response.status_code == 200
    payload = message_response.json()
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert "Relevantne odredbe" in payload["assistant_message"]["content_text"]
    assert payload["retrieval_results"]
    assert payload["assistant_message"]["metadata"]["citations"]

    history_response = client.get(
        f"/api/v1/assistant/sessions/{session['session_id']}/messages"
    )
    assert history_response.status_code == 200
    assert [message["role"] for message in history_response.json()] == [
        "user",
        "assistant",
    ]


def test_assistant_returns_404_for_missing_session(client):
    response = client.post(
        "/api/v1/assistant/sessions/00000000-0000-0000-0000-000000000000/messages",
        json={"content_text": "Pitanje"},
    )

    assert response.status_code == 404
