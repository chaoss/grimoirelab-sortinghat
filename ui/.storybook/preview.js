import "@mdi/font/css/materialdesignicons.css"
import { app } from "@storybook/vue3"
import vuetify from '../src/plugins/vuetify'
import logger from "../src/plugins/logger";
import errorMessages from "../src/plugins/errors";
import router from "../src/router";
import { store } from "../src/store";

export const decorators = [story => ({
  components: { story },
  template: "<story />",
})];

app.use(vuetify)
app.use(logger)
app.use(errorMessages)
app.use(store)
app.use(router)
