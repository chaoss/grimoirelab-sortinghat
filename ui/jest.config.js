module.exports = {
  preset: "@vue/cli-plugin-unit-jest",
  transformIgnorePatterns: [
    "/node_modules/(?!(@storybook/.*)|(storybook/.*)|(vuetify)|(@mdi))",
  ],
  transform: {
    "^.+\\.(ts|js|mjs|cjs)x?$": "babel-jest",
  },
  moduleNameMapper: {
    "^@storybook/core/(.*)": "<rootDir>/node_modules/@storybook/core/dist/$1",
    "^storybook/internal/(.*)": "<rootDir>/node_modules/storybook/core/$1",
  },
  setupFiles: ["./tests/setup.js"],
};
