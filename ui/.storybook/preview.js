import "@mdi/font/css/materialdesignicons.css";
import Vue from "vue";
import * as _Vuetify from "vuetify/lib";
import { configure, addDecorator } from "@storybook/vue";

const Vuetify = _Vuetify.default;

const isVueComponent = obj => obj.name === "VueComponent";

const VComponents = Object.keys(_Vuetify).reduce((acc, key) => {
  if (isVueComponent(_Vuetify[key])) {
    acc[key] = _Vuetify[key];
  }
  return acc;
}, {});

Vue.use(Vuetify, {
  components: {
    ...VComponents
  }
});

const VuetifyConfig = new Vuetify({
  icons: {
    iconfont: "mdi"
  },
  theme: {
    themes: {
      light: {
        primary: "#003756",
        secondary: "#f4bc00"
      }
    }
  }
});

addDecorator(() => ({
  vuetify: VuetifyConfig,
  template: "<v-app><story/></v-app>"
}));
