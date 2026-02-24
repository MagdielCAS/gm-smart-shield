from pytest_bdd import scenario, given, when, then
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def context():
    return {}

@scenario("../health_check.feature", "Check if the API is running")
def test_health_check():
    pass

@given("the API is running")
def api_running(client: TestClient):
    pass

@when("I request the health endpoint")
def request_health(client: TestClient, context):
    context["response"] = client.get("/health")

@then("the response status code should be 200")
def check_status(context):
    assert context["response"].status_code == 200

@then('the response should contain "ok"')
def check_content(context):
    assert context["response"].json()["status"] == "ok"
