import Identity from "./Identity.vue";

export default {
  title: "Identity",
  excludeStories: /.*Data$/
};

const identityTemplate =
  '<identity :uuid="uuid" :name="name" :email="email" :username="username" :source="source" :is-main="isMain"/>';

export const Default = () => ({
  components: { Identity },
  template: identityTemplate,
  props: {
    uuid: {
      default: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6"
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
      default: null
    },
    isMain: {
      default: false
    }
  }
});

export const Source = () => ({
  components: { Identity },
  template: identityTemplate,
  props: {
    uuid: {
      default: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6"
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
    },
    isMain: {
      default: false
    }
  }
});

export const MainIdentity = () => ({
  components: { Identity },
  template: identityTemplate,
  props: {
    uuid: {
      default: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6"
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
      default: "git"
    },
    isMain: {
      default: true
    }
  }
});
