import { storiesOf } from "@storybook/vue";

import Identity from "./Identity.vue";

export default {
  title: "Identity",
  excludeStories: /.*Data$/
};

const identityTemplate =
  '<identity :uuid="uuid" :name="name" :email="email" :username="username" :source="source"/>';

export const Default = () => ({
  components: { Identity },
  template: identityTemplate,
  props: {
    uuid: {
      default: "10f546"
    },
    name: {
      default: "Tom Marvolo Riddle"
    },
    email: {
      default: "triddle@example.net"
    },
    username: {
      default: "triddle"
    }
  }
});

export const Source = () => ({
  components: { Identity },
  template: identityTemplate,
  props: {
    uuid: {
      default: "10f546"
    },
    name: {
      default: "Tom Marvolo Riddle"
    },
    email: {
      default: "triddle@example.net"
    },
    username: {
      default: "triddle"
    },
    source: {
      default: "github"
    }
  }
});
