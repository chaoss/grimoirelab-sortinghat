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
        {
          profile: {
            id: "1",
            name: "Tom Marvolo Riddle"
          }
        },
        {
          profile: {
            id: "2",
            name: "Harry Potter"
          }
        },
        {
          profile: {
            id: "3",
            name: "Voldemort"
          }
        },
        {
          profile: {
            id: "4",
            name: "Hermione Granger"
          }
        },
        {
          profile: {
            id: "5",
            name: "Ambus Dumbledore"
          }
        },
        {
          profile: {
            id: "6",
            name: "Ron Weasley"
          }
        },
        {
          profile: {
            id: "7",
            name: "Severus Snape"
          }
        },
        {
          profile: {
            id: "8",
            name: "Hagrid"
          }
        }
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
