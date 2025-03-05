module.exports = {
  preset: "@vue/cli-plugin-unit-jest",
  transformIgnorePatterns: [
    "/node_modules/(?!(@storybook/.*)|(storybook/.*)|(vuetify)|(@mdi))",
  ],
  transform: {
    "^.+\\.(ts|js|mjs|cjs)x?$": "babel-jest",
  },
  moduleNameMapper: {
    "^vuetify/components$":
      "<rootDir>/node_modules/vuetify/lib/components/index.mjs",
    "^vuetify/directives$":
      "<rootDir>/node_modules/vuetify/lib/directives/index.mjs",
    "^vuetify/labs/VConfirmEdit":
      "<rootDir>/node_modules/vuetify/lib/labs/VConfirmEdit/index.mjs",
    "^vuetify/styles": "<rootDir>/node_modules/vuetify/lib/styles/main.css",
    "^vuetify/iconsets/fa-svg":
      "<rootDir>/node_modules/vuetify/lib/iconsets/fa-svg.mjs",
    "^vuetify/iconsets/mdi":
      "<rootDir>/node_modules/vuetify/lib/iconsets/mdi.mjs",
    "^@storybook/core/(.*)": "<rootDir>/node_modules/@storybook/core/dist/$1",
    "^storybook/internal/(.*)": "<rootDir>/node_modules/storybook/core/$1",
  },
  setupFiles: ["./tests/setup.js"],
};
