const path = require("path");

module.exports = {
  stories: ["../src/components/**/*.stories.js"],
  addons: ["@storybook/addon-actions", "@storybook/addon-links"],
  webpackFinal: async (config, { configType }) => {
    // `configType` has a value of 'DEVELOPMENT' or 'PRODUCTION'
    // You can change the configuration based on that.
    // 'PRODUCTION' is used when building the static version of storybook.

    const VuetifyLoaderPlugin = require("vuetify-loader/lib/plugin");

    config.plugins.push(new VuetifyLoaderPlugin());

    config.module.rules.push({
      test: /\.s(a|c)ss$/,
      use: ["style-loader", "css-loader", "sass-loader"],
      include: path.resolve(__dirname, "../")
    });

    config.resolve.extensions.push(".sass", ".scss");

    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(__dirname, "../src"),
      "~": path.resolve(__dirname, "../src/components")
    };

    // Return the altered config
    return config;
  }
};
