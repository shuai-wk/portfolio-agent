def test_ask(client) -> None:
    response = client.post("/api/ask", json={"question": "你的技术栈是什么？"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "mock answer"
    assert body["sources"][0]["content"] == "doc one"


def test_health_agent(client) -> None:
    response = client.get("/health/agent")

    assert response.status_code == 200
    assert response.json() == {"nodes": ["agent"]}
