import { createApolloProvider } from "@vue/apollo-option";
import {
  ApolloClient,
  ApolloLink,
  createHttpLink,
  InMemoryCache,
  defaultDataIdFromObject,
} from "@apollo/client/core";
import { onError } from "@apollo/client/link/error";
import Cookies from "js-cookie";

const AUTHENTICATION_ERROR = "Authentication credentials were not provided";

export default function setupApolloProvider(apiURL, router, store) {
  // HTTP connection to the API
  const httpLink = createHttpLink({
    uri: apiURL,
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

  const logoutLink = onError(({ graphQLErrors }) => {
    if (graphQLErrors && graphQLErrors[0].message == AUTHENTICATION_ERROR) {
      store.dispatch("logout", {
        redirect: router.currentRoute?.value?.fullPath,
      });
    }
  });

  const link = ApolloLink.from([AuthLink, logoutLink, httpLink]);

  // Create the apollo client
  const apolloClient = new ApolloClient({
    link: link,
    cache,
  });

  const apolloProvider = new createApolloProvider({
    defaultClient: apolloClient,
  });

  return apolloProvider;
}
