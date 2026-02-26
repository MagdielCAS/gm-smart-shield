Feature: Notes API flow

  Scenario: Create, update, and enrich note with tags and source links
    Given the API is running for notes
    When I create a note with markdown frontmatter and hashtags
    And I update the created note with refined content and source links
    Then the updated note should include merged metadata and extracted tags
    And the updated note should expose linked source metadata
