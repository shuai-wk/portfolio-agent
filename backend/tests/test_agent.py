def test_node_names(fake_agent) -> None:
    assert fake_agent.node_names() == ["agent"]


def test_invoke_returns_answer_and_sources(fake_agent, fake_tracer) -> None:
    result = fake_agent.invoke("你的技术栈是什么？")

    assert result["answer"] == "mock answer"
    assert [source["id"] for source in result["sources"]] == [1, 2]
    assert result["sources"][0]["content"] == "doc one"
    assert len(fake_tracer.generations) == 1
    assert fake_tracer.generations[0].output == "mock answer"

