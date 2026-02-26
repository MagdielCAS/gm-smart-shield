Feature: Background Agents
  As a GM
  I want my uploaded rulebooks to be automatically analyzed
  So that I can get character sheet templates and quick reference cards without manual work

  Scenario: Extracting character templates from a rulebook
    Given the knowledge base contains a file "DungeonMasterGuide.pdf"
    When the ingestion background pipeline task completes
    Then a CharacterSheetTemplate should be stored in the database for that source
    And the template should contain "system" and "template_schema"

  Scenario: Extracting quick reference items
    Given the knowledge base contains a file "Spells.txt"
    When the reference extraction task runs
    Then the system should identify "Fireball" as a "Spell"
    And a QuickReference record should be created
