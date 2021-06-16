var path = require('path');

module.exports = {
  publicPath: "/",
  outputDir: path.resolve(__dirname, "../sortinghat/", "core", "static"),
  indexPath: path.resolve(__dirname, "../sortinghat", "core", "templates", "index.html"),
  transpileDependencies: ["vuetify"]
};
