import vuetify from '../src/plugins/vuetify'
import logger from '../src/plugins/logger';
import errorMessages from "../src/plugins/errors";
import dateFormatter from '../src/plugins/dateFormatter';
import router from "../src/router";
import { store } from '../src/store';
import { setup } from '@storybook/vue3';

setup((app) => {
  app.use(vuetify)
  app.use(logger)
  app.use(errorMessages)
  app.use(dateFormatter)
  app.use(store)
  app.use(router)
});
