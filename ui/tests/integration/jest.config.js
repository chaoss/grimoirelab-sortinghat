module.exports = {
  preset: 'jest-puppeteer',
  moduleFileExtensions: [
    'js',
  ],
  testMatch: [
    '**/tests/integration/*.spec.js',
  ],
  verbose: false,
  testTimeout: 20000
};
