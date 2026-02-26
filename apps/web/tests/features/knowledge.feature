Feature: Knowledge Base UI Status and Refresh
  As a user, I want to see the progress of my knowledge source ingestion so that I know when it's ready to use.

  Scenario: View knowledge sources list and status
    Given the knowledge base has existing sources
    When I navigate to the knowledge page
    Then I should see a list of knowledge sources
    And I should see status badges for each source (e.g., "Completed", "Running")

  @fixme
  Scenario: Ingest a new file and see progress
    Given I have selected a file "/docs/new_monster.md"
    When I click the "Add Source" button
    Then I should see the new source appear in the list with status "Pending" or "Running"
    And I should see a progress bar for the running task
    And I should see an estimated time remaining message

  Scenario: Refresh an existing source
    Given I have a "Completed" knowledge source in the list
    When I click the "Refresh" button for that source
    Then the status badge should change to "Pending" or "Running"
    And I should see a loading spinner or progress indicator
