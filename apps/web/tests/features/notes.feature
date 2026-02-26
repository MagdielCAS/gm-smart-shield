Feature: Notes workflows

  Scenario: GM creates note
    Given notes API responses are mocked
    And I am on the notes page
    When I create a note titled "Session One"
    Then I should see the note "Session One" in the list

  Scenario: GM edits note
    Given notes API responses are mocked
    And I am on the notes page
    When I edit note "Session One" with content "Updated mystery thread"
    Then the notes API should receive an update for "Session One"

  Scenario: GM accepts AI suggestion
    Given notes API responses are mocked
    And I am on the notes page
    When I trigger inline AI suggestion for punctuation
    Then I should see a ghost suggestion hint

  Scenario: GM adds reference link
    Given notes API responses are mocked
    And I am on the notes page
    When I run add reference link from the note context menu
    Then I should see an add reference preview
