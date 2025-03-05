import "@mdi/font/css/materialdesignicons.css";
import "vuetify/styles";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import { fa } from "vuetify/iconsets/fa-svg";
import { aliases, mdi } from "vuetify/iconsets/mdi";
import GerritIcon from "../components/GerritIcon.vue";

const customAliases = {
  ...aliases,
  gerrit: GerritIcon,
};

export default createVuetify({
  directives,
  components,
  icons: {
    defaultSet: "mdi",
    aliases: customAliases,
    sets: {
      mdi,
      fa,
    },
  },
  theme: {
    themes: {
      light: {
        colors: {
          primary: "#003756",
          "on-primary": "#ffffff",
          secondary: "#f4bc00",
          "on-secondary": "#001f25",
          finished: "#3fa500",
          failed: "#f41900",
          background: "#ffffff",
          "on-background": "#001f25",
          "surface-secondary": "#f8fdff",
          "on-surface": "#001f25",
          "surface-variant": "#dee3eb",
          "on-surface-variant": "#42474e",
        },
      },
      variables: {
        "border-color": "#f8fdff",
        "border-opacity": 0.12,
      },
    },
  },
  defaults: {
    VAlert: {
      variant: "tonal",
    },
    VBtn: {
      variant: "outlined",
      size: "small",
    },
    VCombobox: {
      variant: "outlined",
      density: "comfortable",
    },
    VDialog: {
      VBtn: {
        size: "default",
      },
    },
    VTextField: {
      variant: "outlined",
      density: "comfortable",
    },
    VSelect: {
      variant: "outlined",
      density: "comfortable",
    },
  },
});
