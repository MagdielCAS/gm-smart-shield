Feature: Health Check

  Scenario: Check if the API is running
    Given the API is running
    When I request the health endpoint
    Then the response status code should be 200
    And the response should contain "ok"
