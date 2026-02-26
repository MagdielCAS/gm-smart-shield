from pytest_bdd import scenario, given, when, then, parsers
from unittest.mock import patch


@scenario("../chat.feature", "Ask a question and get a grounded answer")
def test_chat_grounded_answer():
    pass


@given(parsers.parse('the knowledge base contains information about "{topic}"'))
def mock_knowledge_base(topic):
    # This is handled by mocking the query_knowledge service in the when step
    pass


@when(parsers.parse('I ask "{query}"'), target_fixture="response")
def ask_question(client, query):
    with patch("gm_shield.features.chat.service.query_knowledge") as mock_query:
        with patch(
            "gm_shield.features.chat.service._chat_service.agent.process"
        ) as mock_process:
            # Mock retrieval
            mock_query.return_value = [
                {
                    "content": "Fireball deals 8d6 fire damage.",
                    "metadata": {"source": "phb.pdf"},
                    "score": 0.1,
                }
            ]

            # Mock agent process
            from gm_shield.shared.ai.base import AgentResponse

            async def mock_agent_process(query, context, citations, **kwargs):
                return AgentResponse(
                    text="According to the manual, a fireball spell deals 8d6 fire damage.",
                    citations=citations,
                    metadata={},
                )

            mock_process.side_effect = mock_agent_process

            payload = {"query": query}
            response = client.post("/api/v1/chat/", json=payload)
            return response


@then(
    parsers.parse(
        'the agent should respond with an answer containing "{expected_text}"'
    )
)
def check_answer(response, expected_text):
    assert response.status_code == 200
    data = response.json()
    assert expected_text in data["text"]


@then("the response should include a citation to the source document")
def check_citations(response):
    data = response.json()
    assert len(data["citations"]) > 0
    assert data["citations"][0]["source"] == "phb.pdf"
