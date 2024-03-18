const logger = {
  install(app) {
    function log(type, message, ...args) {
      if (process.env.NODE_ENV === "production" && type === "debug") {
        return;
      }
      /* eslint-disable no-console */
      console[type](message, ...args);
    }

    app.config.globalProperties.$logger = {
      error: (message, ...rest) => log("error", message, ...rest),
      debug: (message, ...rest) => log("debug", message, ...rest),
      log: (message, ...rest) => log("log", message, ...rest),
      info: (message, ...rest) => log("info", message, ...rest),
      warn: (message, ...rest) => log("warn", message, ...rest),
    };
  },
};

export default logger;
