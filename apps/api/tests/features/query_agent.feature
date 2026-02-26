Feature: Query Agent

  Scenario: Stream a simple answer
    Given the knowledge base is ready
    When I ask "What is a short rest?"
    Then I should receive a streaming response
