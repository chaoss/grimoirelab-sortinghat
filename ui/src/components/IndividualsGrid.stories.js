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
          },
          identities: [
            {
              source: "GitLab"
            },
          ]
        },
        {
          profile: {
            id: "2",
            name: "Harry Potter"
          },
          identities: [
            {
              source: "GitHub"
            },
            {
              source: "git"
            },
            {
              source: "Others"
            }
          ]
        },
        {
          profile: {
            id: "3",
            name: "Voldemort"
          },
          identities: [
            {
              source: "GitLab"
            },
          ]
        },
        {
          profile: {
            id: "4",
            name: "Hermione Granger"
          },
          identities: [
            {
              source: "GitHub"
            },
            {
              source: "git"
            },
            {
              source: "Others"
            }
          ]
        },
        {
          profile: {
            id: "5",
            name: "Ambus Dumbledore"
          },
          identities: [
            {
              source: "GitHub"
            },
            {
              source: "git"
            }
          ]
        },
        {
          profile: {
            id: "6",
            name: "Ron Weasley"
          },
          identities: [
            {
              source: "GitHub"
            },
            {
              source: "git"
            },
            {
              source: "Others"
            }
          ]
        },
        {
          profile: {
            id: "7",
            name: "Severus Snape"
          },
          identities: [
            {
              source: "GitLab"
            },
            {
              source: "GitHub"
            },
            {
              source: "git"
            }
          ]
        },
        {
          profile: {
            id: "8",
            name: "Hagrid"
          },
          identities: [
            {
              source: "Git"
            },
            {
              source: "Others"
            }
          ]
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
    },
    sources: {
      default: () => []
    }
  }
});
