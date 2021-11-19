var path = require('path');
const { argv } = require('yargs');

module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: path.resolve(__dirname, "../sortinghat/", "core", "static"),
  indexPath: path.resolve(__dirname, "../sortinghat", "core", "templates", "index.html"),
  transpileDependencies: ["vuetify"],
  productionSourceMap: false,
  chainWebpack: config => {
    config.plugin('define').tap(options => {
      if (argv.api_url) {
        options[0]['process.env'].VUE_APP_API_URL = `"${argv.api_url}"`;
      }
      return options;
    })
  }
};
