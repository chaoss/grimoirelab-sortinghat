export default {
  install(Vue) {
    const ERRORS = {
      14: `The individual is already enrolled in the organization on the
        selected dates.`,
      129: `Invalid credentials. Please check your username and password and
        try again.`
    };

    Vue.prototype.$getErrorMessage = error => {
      if (error.graphQLErrors && error.graphQLErrors.length > 0) {
        return error.graphQLErrors
          .map(error => {
            const code = error.extensions.code;
            return ERRORS[code] || error.message;
          })
          .join(". ");
      } else if (error.networkError) {
        if (error.networkError.result) {
          return error.networkError.result.errors
            .map(error => error.message)
            .join(". ");
        } else {
          return error.networkError.message;
        }
      }
      return error.message;
    };
  }
};
