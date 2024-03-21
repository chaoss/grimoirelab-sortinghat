const path = require("path");

module.exports = {
  "stories": [
    "../src/**/*.stories.js"
  ],
  "framework": {
    name: "@storybook/vue3-webpack5",
    options: {}
  },
  webpackFinal: async (config, { configType }) => {
    config.module.rules.push(
      {
      test: /\.scss$/,
      use: ['style-loader', 'css-loader', 'sass-loader'],
      include: path.resolve(__dirname, '../'),
    });

      config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(__dirname, "../src"),
      "~": path.resolve(__dirname, "../src/components")
    };

    // Return the altered config
    return config;
  },
  addons: ["@storybook/addon-webpack5-compiler-babel"]
}
