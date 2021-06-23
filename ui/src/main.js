import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import vuetify from "./plugins/vuetify";
import VueApollo from "vue-apollo";
import VueRouter from "vue-router";
import { ApolloClient } from "apollo-client";
import { createHttpLink } from "apollo-link-http";
import { InMemoryCache } from "apollo-cache-inmemory";
import Cookies from "js-cookie";
import { ApolloLink } from "apollo-link";
import Logger from "./plugins/logger";
import GetErrorMessage from "./plugins/errors";

// Force HTTP GET to the Django Server for getting the csrf token
fetch("/api/", { credentials: "include" }).then(() => {
  const csrftoken = Cookies.get("csrftoken");

  // HTTP connection to the API
  const uri = `/api/`;
  const httpLink = createHttpLink({
    uri,
    credentials: "include"
  });

  // Cache implementation
  const cache = new InMemoryCache();

  const AuthLink = (operation, next) => {
    const token = csrftoken;
    const authtoken = Cookies.get("sh_authtoken");
    operation.setContext(context => ({
      ...context,
      headers: {
        ...context.headers,
        "X-CSRFToken": token,
        Authorization: authtoken ? `JWT ${authtoken}` : ""
      }
    }));
    return next(operation);
  };

  const link = ApolloLink.from([AuthLink, httpLink]);

  // Create the apollo client
  const apolloClient = new ApolloClient({
    link: link,
    cache
  });

  Vue.use(VueApollo);
  Vue.use(VueRouter);
  Vue.use(Logger);
  Vue.use(GetErrorMessage);

  const apolloProvider = new VueApollo({
    defaultClient: apolloClient
  });

  Vue.config.productionTip = false;

  new Vue({
    router,
    store,
    vuetify,
    apolloProvider,
    render: h => h(App)
  }).$mount("#app");
});
