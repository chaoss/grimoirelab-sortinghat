import { storiesOf } from "@storybook/vue";

import IndividualCard from "./IndividualCard.vue";

export default {
  title: "IndividualCard",
  excludeStories: /.*Data$/
};

const individualCardTemplate = '<individual-card :name="name" />';

export const Default = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    }
  }
});
export const SingleInitial = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Voldemort"
    }
  }
});
