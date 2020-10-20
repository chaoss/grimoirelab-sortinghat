import { storiesOf } from "@storybook/vue";

import IndividualCard from "./IndividualCard.vue";

export default {
  title: "IndividualCard",
  excludeStories: /.*Data$/
};

const individualCardTemplate = `
  <individual-card
    :name="name"
    :sources="sources"
    :is-locked="isLocked"
    :uuid="uuid"
    :identities="identities"
    :enrollments="enrollments"
    />`;

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
    },
    identities: [],
    enrollments: []
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
    },
    identities: [],
    enrollments: []
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
    },
    identities: {
      default: () => [
        {
          name: "GitLab",
          identities: [
            {
              name: "Tom Marvolo Riddle",
              source: "GitLab",
              email: "triddle@example.net",
              uuid: "03b3428ee",
              username: "triddle"
            }
          ]
        },
        {
          name: "GitHub",
          identities: [
            {
              uuid: "808b18",
              name: "Voldemort",
              email: "-",
              username: "voldemort",
              source: "github"
            }
          ]
        },
        {
          name: "git",
          identities: [
            {
              uuid: "006afa",
              name: "Tom Marvolo Riddle",
              email: "triddle@example.net",
              username: "triddle",
              source: "git"
            },
            {
              uuid: "abce32",
              name: "voldemort",
              email: "voldemort@example.net",
              username: "-",
              source: "git"
            }
          ]
        }
      ]
    },
    enrollments: {
      default: () => [
        {
          organization: {
            name: "Slytherin",
            id: "2"
          },
          start: "1938-09-01T00:00:00+00:00",
          end: "1998-05-02T00:00:00+00:00"
        },
        {
          organization: {
            name: "Hogwarts School of Witchcraft and Wizardry",
            id: "1"
          },
          start: "1938-09-01",
          end: "1945-06-02T00:00:00+00:00"
        }
      ]
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
    },
    identities: [],
    enrollments: []
  }
});
