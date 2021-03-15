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
          isLocked: true,
          profile: {
            id: "1",
            name: "Tom Marvolo Riddle"
          },
          identities: [
            {
              source: "GitLab",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "2",
            name: "Harry Potter"
          },
          identities: [
            {
              source: "GitHub",
              uuid: "10f546"
            },
            {
              source: "git",
              uuid: "10f546"
            },
            {
              source: "Others",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "3",
            name: "Voldemort"
          },
          identities: [
            {
              source: "GitLab",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "4",
            name: "Hermione Granger"
          },
          identities: [
            {
              source: "GitHub",
              uuid: "10f546"
            },
            {
              source: "git",
              uuid: "10f546"
            },
            {
              source: "Others",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "5",
            name: "Ambus Dumbledore"
          },
          identities: [
            {
              source: "GitHub",
              uuid: "10f546"
            },
            {
              source: "git",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "6",
            name: "Ron Weasley"
          },
          identities: [
            {
              source: "GitHub",
              uuid: "10f546"
            },
            {
              source: "git",
              uuid: "10f546"
            },
            {
              source: "Others",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "7",
            name: "Severus Snape"
          },
          identities: [
            {
              source: "GitLab",
              uuid: "10f546"
            },
            {
              source: "GitHub",
              uuid: "10f546"
            },
            {
              source: "git",
              uuid: "10f546"
            }
          ]
        },
        {
          isLocked: false,
          profile: {
            id: "8",
            name: "Hagrid"
          },
          identities: [
            {
              source: "Git",
              uuid: "10f546"
            },
            {
              source: "Others",
              uuid: "10f546"
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
