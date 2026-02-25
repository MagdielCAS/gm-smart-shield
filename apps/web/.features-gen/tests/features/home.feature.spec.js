// Generated from: tests/features/home.feature
import { test } from "playwright-bdd";

test.describe('Home Page', () => {

  test('Visit Home Page', async ({ Given, Then, page }) => {
    await Given('I am on the home page', null, { page });
    await Then('I should see "Welcome to GM Smart Shield"', null, { page });
  });

});

// == technical section ==

test.use({
  $test: [({}, use) => use(test), { scope: 'test', box: true }],
  $uri: [({}, use) => use('tests/features/home.feature'), { scope: 'test', box: true }],
  $bddFileData: [({}, use) => use(bddFileData), { scope: "test", box: true }],
});

const bddFileData = [ // bdd-data-start
  {"pwTestLine":6,"pickleLine":3,"tags":[],"steps":[{"pwStepLine":7,"gherkinStepLine":4,"keywordType":"Context","textWithKeyword":"Given I am on the home page","stepMatchArguments":[]},{"pwStepLine":8,"gherkinStepLine":5,"keywordType":"Outcome","textWithKeyword":"Then I should see \"Welcome to GM Smart Shield\"","stepMatchArguments":[{"group":{"start":13,"value":"\"Welcome to GM Smart Shield\"","children":[{"start":14,"value":"Welcome to GM Smart Shield","children":[{"children":[]}]},{"children":[{"children":[]}]}]},"parameterTypeName":"string"}]}]},
]; // bdd-data-end