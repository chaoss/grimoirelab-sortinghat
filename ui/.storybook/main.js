const path = require("path");
const { VuetifyPlugin } = require("webpack-plugin-vuetify");

module.exports = {
  "stories": [
    "../src/**/*.stories.js"
  ],
  "framework": "@storybook/vue3",
  "core": {
    "builder": "@storybook/builder-webpack5"
  },
  webpackFinal: async (config, { configType }) => {
    const { VueLoaderPlugin } = require("vue-loader");

    const VueLoader = new VueLoaderPlugin();
    const Vuetify = new VuetifyPlugin();

    config.plugins.push(VueLoader);
    config.plugins.push(Vuetify)

    config.module.rules.push(
      {
        test: /\.vue$/,
        use: "vue-loader",
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
      "vue": "vue/dist/vue.cjs.js"
    };

    // Return the altered config
    return config;
  }
}
