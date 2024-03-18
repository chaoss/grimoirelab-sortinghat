const path = require("path");
const { argv } = require("yargs");
const { VuetifyPlugin } = require("webpack-plugin-vuetify");

module.exports = {
  publicPath: argv.publicpath
    ? argv.publicpath
    : process.env.NODE_ENV === "production"
    ? "/identities/"
    : "/",
  outputDir: path.resolve(__dirname, "../sortinghat/", "core", "static"),
  indexPath: path.resolve(
    __dirname,
    "../sortinghat",
    "core",
    "templates",
    "index.html"
  ),
  transpileDependencies: ["vuetify"],
  productionSourceMap: false,
  chainWebpack: (config) => {
    config.plugin("define").tap((options) => {
      if (argv.api_url) {
        options[0]["process.env"].VUE_APP_API_URL = `"${argv.api_url}"`;
      }
      return options;
    });

    config.plugin("define").tap((definitions) => {
      Object.assign(definitions[0], {
        __VUE_OPTIONS_API__: "true",
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
      });
      return definitions;
    });
  },
  configureWebpack: {
    plugins: [new VuetifyPlugin()],
    devtool: "source-map",
  },
};
