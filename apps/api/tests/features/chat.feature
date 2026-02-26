Feature: Chat with Knowledge Agent
  As a Game Master
  I want to ask questions to the AI assistant
  So that I can quickly reference rules and lore during my game

  Scenario: Ask a question and get a grounded answer
    Given the knowledge base contains information about "fireball spells"
    When I ask "What is the damage of a fireball spell?"
    Then the agent should respond with an answer containing "8d6 fire damage"
    And the response should include a citation to the source document
