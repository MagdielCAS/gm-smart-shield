Feature: Tagging Agent

  Scenario: Auto-tagging a saved note
    Given I have a note titled "Sewer Encounter"
    When I save the note with content "The group fights the Wererat King."
    Then the system should generate a background task for tagging
    And eventually the note should contain the tag "Wererat"
