const path = require("path");

module.exports = {
  "stories": [
    "../src/**/*.stories.js"
  ],
  "framework": "@storybook/vue",
  "core": {
    "builder": "@storybook/builder-webpack5"
  },
  webpackFinal: async (config, { configType }) => {
    // Use vue-loader 15.x because the default 17.x is incompatible with Vue 2
    const { VueLoaderPlugin } = require("@vue/vue-loader-v15");

    const VueLoader = new VueLoaderPlugin();

    config.plugins.push(VueLoader);

    config.module.rules.push(
      {
        test: /\.vue$/,
        use: "@vue/vue-loader-v15",
        include: path.resolve(__dirname, "../")
      },
      {
        test: /\.s(a|c)ss$/,
        use: ["style-loader", "css-loader", "sass-loader"],
        include: path.resolve(__dirname, "../")
      }
    );

    config.resolve.extensions.push(".sass", ".scss", ".vue");

    // Resolve "vue" to the compiler-included build instead of runtime
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(__dirname, "../src"),
      "~": path.resolve(__dirname, "../src/components"),
      "vue": "vue/dist/vue.js"
    };

    // Return the altered config
    return config;
  }
}
