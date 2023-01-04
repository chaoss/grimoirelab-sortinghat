const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:8000",
    screenshotOnRunFailure: false,
    specPattern: "tests/e2e/specs/**/*.cy.{js,jsx,ts,tsx}",
    supportFile: "tests/e2e/support/index.js",
    defaultCommandTimeout: 20000,
    pageLoadTimeout: 20000,
    requestTimeout: 20000,
    video: false
  }
});
