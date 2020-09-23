import { storiesOf } from "@storybook/vue";

import IndividualCard from "./IndividualCard.vue";

export default {
  title: "IndividualCard",
  excludeStories: /.*Data$/
};

const individualCardTemplate = '<individual-card :name="name" :sources="sources" :is-locked="isLocked" :uuid="uuid" />';

export const Default = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    sources: {
      default: () => []
    },
    isLocked: {
      default: false
    },
    uuid: {
      default: "10f546"
    }
  }
});
export const SingleInitial = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Voldemort"
    },
    sources: {
      default: () => []
    },
    isLocked: {
      default: false
    },
    uuid: {
      default: "10f546"
    }
  }
});
export const Sources = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    sources: {
      default: () => [
        'git',
        'github',
        'gitlab',
        'others'
      ]
    },
    isLocked: {
      default: false
    },
    uuid: {
      default: "10f546"
    }
  }
});
export const Locked = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    sources: {
      default: () => []
    },
    isLocked: {
      default: true
    },
    uuid: {
      default: "10f546"
    }
  }
});
