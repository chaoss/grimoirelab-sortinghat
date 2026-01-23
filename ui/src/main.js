import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { store } from "./store";
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { far } from "@fortawesome/free-regular-svg-icons";
import { fab } from "@fortawesome/free-brands-svg-icons";
import vuetify from "./plugins/vuetify";
import logger from "./plugins/logger";
import errorMessages from "./plugins/errors";
import dateFormatter from "./plugins/dateFormatter";
import setupApolloProvider from "./apollo/provider";

const API_URL = process.env.VUE_APP_API_URL || `${process.env.BASE_URL}api/`;

const apolloProvider = setupApolloProvider(API_URL, router, store);

createApp(App)
  .component("font-awesome-icon", FontAwesomeIcon)
  .use(apolloProvider)
  .use(dateFormatter)
  .use(errorMessages)
  .use(logger)
  .use(store)
  .use(router)
  .use(vuetify)
  .mount("#app");

// Add FontAwesome icons
library.add(far);
library.add(fab);
