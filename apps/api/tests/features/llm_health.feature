Feature: LLM Health Check

  Scenario: System check returns ready when all models are available
    Given Ollama is running and models are available
    When I GET "/api/v1/system/llm-health"
    Then the response status code should be 200
    And the response status field should be "ready"
