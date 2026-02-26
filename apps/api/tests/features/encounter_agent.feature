Feature: Encounter Agent
  As a GM
  I want to generate balanced combat encounters
  So that I can quickly set up battles without hours of prep

  Scenario: Generating a standard encounter
    Given the RAG knowledge base is active
    When I request an encounter for "Level 5", "Hard", "Swamp ambush"
    Then the response should contain a "title"
    And the response should contain a "description"
    And the response should contain at least 1 NPC stat block
    And the NPC stat block should have "hp" and "ac"
