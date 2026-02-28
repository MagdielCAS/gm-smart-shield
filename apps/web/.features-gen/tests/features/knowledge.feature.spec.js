// Generated from: tests/features/knowledge.feature
import { test } from "playwright-bdd";

test.describe('Knowledge Base UI Status and Refresh', () => {

  test('View knowledge sources list and status', async ({ Given, When, Then, And, page }) => { 
    await Given('the knowledge base has existing sources', null, { page }); 
    await When('I navigate to the knowledge page', null, { page }); 
    await Then('I should see a list of knowledge sources', null, { page }); 
    await And('I should see status badges for each source (e.g., "Completed", "Running")', null, { page }); 
  });

  test.fixme('Ingest a new file and see progress', { tag: ['@fixme'] }, async ({ Given, When, Then, And }) => { 
    await Given('I have selected a file "/docs/new_monster.md"'); 
    await When('I click the "Add Source" button'); 
    await Then('I should see the new source appear in the list with status "Pending" or "Running"'); 
    await And('I should see a progress bar for the running task'); 
    await And('I should see an estimated time remaining message'); 
  });

  test('Refresh an existing source', async ({ Given, When, Then, And, page }) => { 
    await Given('I have a "Completed" knowledge source in the list', null, { page }); 
    await When('I click the "Refresh" button for that source', null, { page }); 
    await Then('the status badge should change to "Pending" or "Running"', null, { page }); 
    await And('I should see a loading spinner or progress indicator', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('tests/features/knowledge.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":6,"pickleLine":4,"tags":[],"steps":[{"pwStepLine":7,"gherkinStepLine":5,"keywordType":"Context","textWithKeyword":"Given the knowledge base has existing sources","stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":6,"keywordType":"Action","textWithKeyword":"When I navigate to the knowledge page","stepMatchArguments":[]},{"pwStepLine":9,"gherkinStepLine":7,"keywordType":"Outcome","textWithKeyword":"Then I should see a list of knowledge sources","stepMatchArguments":[]},{"pwStepLine":10,"gherkinStepLine":8,"keywordType":"Outcome","textWithKeyword":"And I should see status badges for each source (e.g., \"Completed\", \"Running\")","stepMatchArguments":[{"group":{"start":50,"value":"\"Completed\"","children":[{"start":51,"value":"Completed","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":63,"value":"\"Running\"","children":[{"start":64,"value":"Running","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":13,"pickleLine":11,"skipped":true,"tags":["@fixme"],"steps":[{"pwStepLine":14,"gherkinStepLine":12,"keywordType":"Context","textWithKeyword":"Given I have selected a file \"/docs/new_monster.md\""},{"pwStepLine":15,"gherkinStepLine":13,"keywordType":"Action","textWithKeyword":"When I click the \"Add Source\" button"},{"pwStepLine":16,"gherkinStepLine":14,"keywordType":"Outcome","textWithKeyword":"Then I should see the new source appear in the list with status \"Pending\" or \"Running\""},{"pwStepLine":17,"gherkinStepLine":15,"keywordType":"Outcome","textWithKeyword":"And I should see a progress bar for the running task"},{"pwStepLine":18,"gherkinStepLine":16,"keywordType":"Outcome","textWithKeyword":"And I should see an estimated time remaining message"}]},
  {"pwTestLine":21,"pickleLine":18,"tags":[],"steps":[{"pwStepLine":22,"gherkinStepLine":19,"keywordType":"Context","textWithKeyword":"Given I have a \"Completed\" knowledge source in the list","stepMatchArguments":[{"group":{"start":9,"value":"\"Completed\"","children":[{"start":10,"value":"Completed","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":23,"gherkinStepLine":20,"keywordType":"Action","textWithKeyword":"When I click the \"Refresh\" button for that source","stepMatchArguments":[]},{"pwStepLine":24,"gherkinStepLine":21,"keywordType":"Outcome","textWithKeyword":"Then the status badge should change to \"Pending\" or \"Running\"","stepMatchArguments":[{"group":{"start":34,"value":"\"Pending\"","children":[{"start":35,"value":"Pending","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":47,"value":"\"Running\"","children":[{"start":48,"value":"Running","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":25,"gherkinStepLine":22,"keywordType":"Outcome","textWithKeyword":"And I should see a loading spinner or progress indicator","stepMatchArguments":[]}]},
]; // bdd-data-end