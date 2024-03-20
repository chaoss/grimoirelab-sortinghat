import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { store } from "./store";
import Cookies from "js-cookie";
import { ApolloLink } from "apollo-link";
import { createApolloProvider } from "@vue/apollo-option";
import {
  ApolloClient,
  createHttpLink,
  InMemoryCache,
  defaultDataIdFromObject,
} from "@apollo/client/core";
import vuetify from "./plugins/vuetify";
import logger from "./plugins/logger";
import errorMessages from "./plugins/errors";

const API_URL = process.env.VUE_APP_API_URL || `${process.env.BASE_URL}api/`;

// HTTP connection to the API
const httpLink = createHttpLink({
  uri: API_URL,
  credentials: "include",
});

// Cache implementation
// Specify object IDs so Apollo can update the cache automatically
// https://www.apollographql.com/docs/react/v2/caching/cache-configuration/#custom-identifiers
const cache = new InMemoryCache({
  dataIdFromObject: (object) => {
    switch (object.__typename) {
      case "IndividualType":
        return object.mk;
      case "IdentityType":
        return object.uuid;
      default:
        return defaultDataIdFromObject(object);
    }
  },
});

const AuthLink = (operation, next) => {
  const csrftoken = Cookies.get("csrftoken");

  operation.setContext((context) => ({
    ...context,
    headers: {
      ...context.headers,
      "X-CSRFToken": csrftoken,
    },
  }));
  return next(operation);
};

const link = ApolloLink.from([AuthLink, httpLink]);

// Create the apollo client
const apolloClient = new ApolloClient({
  link: link,
  cache,
});

const apolloProvider = new createApolloProvider({
  defaultClient: apolloClient,
});

createApp(App)
  .use(apolloProvider)
  .use(errorMessages)
  .use(logger)
  .use(store)
  .use(router)
  .use(vuetify)
  .mount("#app");
