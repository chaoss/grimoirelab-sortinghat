import { storiesOf } from "@storybook/vue";

import IndividualCard from "./IndividualCard.vue";

export default {
  title: "IndividualCard",
  excludeStories: /.*Data$/
};

const individualCardTemplate = '<individual-card :name="name" :sources="sources" />';

export const Default = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    sources: {
      default: () => []
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
    }
  }
});
