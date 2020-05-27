import { storiesOf } from "@storybook/vue";

import IndividualsGrid from "./IndividualsGrid.vue";

export default {
  title: "IndividualsGrid",
  excludeStories: /.*Data$/
};

const individualsGridTemplate =
  '<individuals-grid :individuals="individuals" />';

export const Default = () => ({
  components: { IndividualsGrid },
  template: individualsGridTemplate,
  props: {
    individuals: {
      default: () => [
        "Tom Marvolo Riddle",
        "Harry Potter",
        "Voldemort",
        "Hermione Granger",
        "Ambus Dumbledore",
        "Ron Weasley",
        "Severus Snape",
        "Hagrid"
      ]
    }
  }
});
export const Empty = () => ({
  components: { IndividualsGrid },
  template: individualsGridTemplate,
  props: {
    individuals: {
      default: () => []
    }
  }
});
