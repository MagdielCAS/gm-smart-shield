import pytest
from pytest_bdd import given, when, then, scenarios, parsers
from fastapi.testclient import TestClient
from gm_shield.main import app

# Load scenarios from the feature file
scenarios("../knowledge_status.feature")


@pytest.fixture
def context():
    return {}


@pytest.fixture
def client():
    return TestClient(app)


@given(parsers.parse('I have a valid knowledge source file "{file_path}"'))
def valid_knowledge_source(context, file_path):
    context["file_path"] = file_path


@when("I submit the file for ingestion")
def submit_ingestion(client, context):
    file_path = context["file_path"]
    response = client.post("/api/v1/knowledge/", json={"file_path": file_path})
    context["response"] = response
    # Store the ID if successful
    if response.status_code == 202:
        # Note: Ingestion returns task_id, not source_id directly in the main response model usually,
        # but let's check. The response model has task_id.
        pass


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(context, status_code):
    assert context["response"].status_code == status_code


@then("the response should contain a task ID")
def check_task_id(context):
    data = context["response"].json()
    assert "task_id" in data


@then(parsers.parse('the response status should be "{status}"'))
def check_response_status(context, status):
    data = context["response"].json()
    assert data["status"] == status


# Scenario: List knowledge sources
@given(parsers.parse('I have ingested a knowledge source "{file_path}"'))
def ensure_ingested_source(client, context, file_path):
    # Check if exists first
    response = client.get("/api/v1/knowledge/")
    items = response.json().get("items", [])
    if not any(i["source"] == file_path for i in items):
        client.post("/api/v1/knowledge/", json={"file_path": file_path})


@when("I request the list of knowledge sources")
def request_list(client, context):
    context["response"] = client.get("/api/v1/knowledge/")


@then(parsers.parse('the list should contain "{file_path}"'))
def check_list_contains(context, file_path):
    items = context["response"].json()["items"]
    assert any(i["source"] == file_path for i in items)


@then(
    parsers.parse(
        'the status of "{file_path}" should be "{s1}" or "{s2}" or "{s3}" or "{s4}"'
    )
)
def check_status_options(context, file_path, s1, s2, s3, s4):
    items = context["response"].json()["items"]
    item = next((i for i in items if i["source"] == file_path), None)
    assert item is not None
    assert item["status"] in [s1, s2, s3, s4]


# Scenario: Refresh
@given(parsers.parse("I have an existing knowledge source with ID {source_id:d}"))
def ensure_source_id(client, context, source_id):
    # Ensure a source exists. We'll use a specific path to ensure consistency.
    file_path = f"/docs/source_{source_id}.pdf"

    # Check if it exists and get its real ID
    list_resp = client.get("/api/v1/knowledge/")
    items = list_resp.json().get("items", [])
    existing = next((i for i in items if i["source"] == file_path), None)

    if existing:
        context["source_id"] = existing["id"]
        context["file_path"] = file_path
    else:
        # Create it
        client.post("/api/v1/knowledge/", json={"file_path": file_path})
        # Fetch again to get ID
        list_resp = client.get("/api/v1/knowledge/")
        items = list_resp.json()["items"]
        new_item = next((i for i in items if i["source"] == file_path), None)
        context["source_id"] = new_item["id"]
        context["file_path"] = file_path


@when(parsers.parse("I request to delete knowledge source {source_id:d}"))
def delete_source(client, context, source_id):
    real_id = context.get("source_id", source_id)
    context["response"] = client.delete(f"/api/v1/knowledge/{real_id}")


@then("the knowledge source should no longer exist in the list")
def check_source_deleted(client, context):
    file_path = context.get("file_path")
    list_resp = client.get("/api/v1/knowledge/")
    items = list_resp.json().get("items", [])
    exists = any(i["source"] == file_path for i in items)
    assert not exists, f"Source {file_path} still exists in the list."


@when(parsers.parse("I request to refresh knowledge source {source_id:d}"))
def refresh_source(client, context, source_id):
    # Use the real ID from context if we set it (which we did in the Given step)
    real_id = context.get("source_id", source_id)
    context["response"] = client.post(f"/api/v1/knowledge/{real_id}/refresh")


@then("the response should indicate that refresh has started")
def check_refresh_msg(context):
    data = context["response"].json()
    assert "Refresh started" in data["message"]
