const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:8000",
    defaultCommandTimeout: 6000,
    requestTimeout: 6000,
    screenshotOnRunFailure: false,
    specPattern: "tests/e2e/specs/**/*.cy.{js,jsx,ts,tsx}",
    supportFile: "tests/e2e/support/index.js",
    video: false,
  },
});
