Feature: Knowledge Base Status and Refresh
  As a GM, I want to track the status of my knowledge sources and refresh them so that I can ensure my AI is up-to-date.

  Scenario: Ingest a new knowledge source and check initial status
    Given I have a valid knowledge source file "/docs/new_monster.md"
    When I submit the file for ingestion
    Then the response status code should be 202
    And the response should contain a task ID
    And the response status should be "pending"

  Scenario: List knowledge sources with status
    Given I have ingested a knowledge source "/docs/rulebook.pdf"
    When I request the list of knowledge sources
    Then the response status code should be 200
    And the list should contain "/docs/rulebook.pdf"
    And the status of "/docs/rulebook.pdf" should be "pending" or "running" or "completed"

  Scenario: Refresh a knowledge source
    Given I have an existing knowledge source with ID 1
    When I request to refresh knowledge source 1
    Then the response status code should be 202
    And the response should indicate that refresh has started
