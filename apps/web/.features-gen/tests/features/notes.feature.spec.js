// Generated from: tests/features/notes.feature
import { test } from "playwright-bdd";

test.describe('Notes workflows', () => {

  test('GM creates note', async ({ Given, When, Then, And, page }) => { 
    await Given('notes API responses are mocked', null, { page }); 
    await And('I am on the notes page', null, { page }); 
    await When('I create a note titled "Session One"', null, { page }); 
    await Then('I should see the note "Session One" in the list', null, { page }); 
  });

  test('GM edits note', async ({ Given, When, Then, And, page }) => { 
    await Given('notes API responses are mocked', null, { page }); 
    await And('I am on the notes page', null, { page }); 
    await When('I edit note "Session One" with content "Updated mystery thread"', null, { page }); 
    await Then('the notes API should receive an update for "Session One"', null, { page }); 
  });

  test('GM accepts AI suggestion', async ({ Given, When, Then, And, page }) => { 
    await Given('notes API responses are mocked', null, { page }); 
    await And('I am on the notes page', null, { page }); 
    await When('I trigger inline AI suggestion for punctuation', null, { page }); 
    await Then('I should see a ghost suggestion hint', null, { page }); 
  });

  test('GM adds reference link', async ({ Given, When, Then, And, page }) => { 
    await Given('notes API responses are mocked', null, { page }); 
    await And('I am on the notes page', null, { page }); 
    await When('I run add reference link from the note context menu', null, { page }); 
    await Then('I should see an add reference preview', null, { page }); 
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('tests/features/notes.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":6,"pickleLine":3,"tags":[],"steps":[{"pwStepLine":7,"gherkinStepLine":4,"keywordType":"Context","textWithKeyword":"Given notes API responses are mocked","stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":5,"keywordType":"Context","textWithKeyword":"And I am on the notes page","stepMatchArguments":[]},{"pwStepLine":9,"gherkinStepLine":6,"keywordType":"Action","textWithKeyword":"When I create a note titled \"Session One\"","stepMatchArguments":[{"group":{"start":23,"value":"\"Session One\"","children":[{"start":24,"value":"Session One","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":10,"gherkinStepLine":7,"keywordType":"Outcome","textWithKeyword":"Then I should see the note \"Session One\" in the list","stepMatchArguments":[{"group":{"start":22,"value":"\"Session One\"","children":[{"start":23,"value":"Session One","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":13,"pickleLine":9,"tags":[],"steps":[{"pwStepLine":14,"gherkinStepLine":10,"keywordType":"Context","textWithKeyword":"Given notes API responses are mocked","stepMatchArguments":[]},{"pwStepLine":15,"gherkinStepLine":11,"keywordType":"Context","textWithKeyword":"And I am on the notes page","stepMatchArguments":[]},{"pwStepLine":16,"gherkinStepLine":12,"keywordType":"Action","textWithKeyword":"When I edit note \"Session One\" with content \"Updated mystery thread\"","stepMatchArguments":[{"group":{"start":12,"value":"\"Session One\"","children":[{"start":13,"value":"Session One","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"},{"group":{"start":39,"value":"\"Updated mystery thread\"","children":[{"start":40,"value":"Updated mystery thread","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]},{"pwStepLine":17,"gherkinStepLine":13,"keywordType":"Outcome","textWithKeyword":"Then the notes API should receive an update for \"Session One\"","stepMatchArguments":[{"group":{"start":43,"value":"\"Session One\"","children":[{"start":44,"value":"Session One","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
  {"pwTestLine":20,"pickleLine":15,"tags":[],"steps":[{"pwStepLine":21,"gherkinStepLine":16,"keywordType":"Context","textWithKeyword":"Given notes API responses are mocked","stepMatchArguments":[]},{"pwStepLine":22,"gherkinStepLine":17,"keywordType":"Context","textWithKeyword":"And I am on the notes page","stepMatchArguments":[]},{"pwStepLine":23,"gherkinStepLine":18,"keywordType":"Action","textWithKeyword":"When I trigger inline AI suggestion for punctuation","stepMatchArguments":[]},{"pwStepLine":24,"gherkinStepLine":19,"keywordType":"Outcome","textWithKeyword":"Then I should see a ghost suggestion hint","stepMatchArguments":[]}]},
  {"pwTestLine":27,"pickleLine":21,"tags":[],"steps":[{"pwStepLine":28,"gherkinStepLine":22,"keywordType":"Context","textWithKeyword":"Given notes API responses are mocked","stepMatchArguments":[]},{"pwStepLine":29,"gherkinStepLine":23,"keywordType":"Context","textWithKeyword":"And I am on the notes page","stepMatchArguments":[]},{"pwStepLine":30,"gherkinStepLine":24,"keywordType":"Action","textWithKeyword":"When I run add reference link from the note context menu","stepMatchArguments":[]},{"pwStepLine":31,"gherkinStepLine":25,"keywordType":"Outcome","textWithKeyword":"Then I should see an add reference preview","stepMatchArguments":[]}]},
]; // bdd-data-end