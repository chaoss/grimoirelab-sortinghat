import { storiesOf } from "@storybook/vue";

import ExpandedIndividual from "./ExpandedIndividual.vue";

export default {
  title: "ExpandedIndividual",
  excludeStories: /.*Data$/
};

const expandedIndividualTemplate = '<expanded-individual :enrollments="enrollments" :identities="identities" :compact="compact" />';

export const Default = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    compact: false,
    name: "Tom Marvolo Riddle",
    identities: [
    {
      name: "GitHub",
      identities: [
        {
          uuid: "006afa",
          name: "Tom Marvolo Riddle",
          email: "triddle@example.net",
          username: "triddle"
        },
        {
          uuid: "808b18",
          name: "Voldemort",
          email: "-",
          username: "voldemort"
        }
      ]
    },
    {
      name: "Git",
      identities: [
        {
          uuid: "abce32",
          name: "voldemort",
          email: "voldemort@example.net",
          username: "-"
        }
      ]
    },
    {
      name: "Others",
      identities: [
        {
          uuid: "4ce562",
          name: "-",
          email: "-",
          username: "voldemort",
          source: "irc"
        }
      ]
    }],
    enrollments: [
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
  })
});

export const Compact = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    compact: true,
    name: "Tom Marvolo Riddle",
    identities: [
    {
      name: "GitHub",
      identities: [
        {
          uuid: "006afa",
          name: "Tom Marvolo Riddle",
          email: "triddle@example.net",
          username: "triddle"
        },
        {
          uuid: "808b18",
          name: "Voldemort",
          email: "-",
          username: "voldemort"
        }
      ]
    },
    {
      name: "Git",
      identities: [
        {
          uuid: "abce32",
          name: "voldemort",
          email: "voldemort@example.net",
          username: "-"
        }
      ]
    },
    {
      name: "Others",
      identities: [
        {
          uuid: "4ce562",
          name: "-",
          email: "-",
          username: "voldemort",
          source: "irc"
        }
      ]
    }],
    enrollments: [
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
  })
});

export const NoOrganizations = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    compact: false,
    identities: [
      {
        name: "Git",
        identities: [
          {
            uuid: "4ce562",
            name: "Hagrid",
            email: "hagrid@example.com",
            username: "hagrid"
          }
        ]
      },
    ],
    enrollments: []
  })
});
