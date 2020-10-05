import { storiesOf } from "@storybook/vue";

import IndividualsTable from "./IndividualsTable.vue";

export default {
  title: "IndividualsTable",
  excludeStories: /.*Data$/
};

const IndividualsTableTemplate = '<individuals-table :individuals="individuals" />';

export const Default = () => ({
  components: { IndividualsTable },
  template: IndividualsTableTemplate,
  data: () => ({
    individuals: [
      {
        id: 1,
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [ "github", "git", "others" ],
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
      },
      {
        id: 2,
        name: "Harry Potter",
        organization: "Griffyndor",
        email: "hpotter@example.com",
        sources: [ "git", "gitlab", "github", "others" ],
        identities: [
        {
          name: "Git",
          identities: [
            {
              uuid: "006afa",
              name: "Harry Potter",
              email: "hpotter@example.net",
              username: "-"
            }
          ]
        },
        {
          name: "GitHub",
          identities: [
            {
              uuid: "4ce562",
              name: "H. Potter",
              email: "hpotter@example.net",
              username: "potter"
            }
          ]
        },
        {
          name: "GitLab",
          identities: [
            {
              uuid: "808b18",
              name: "Harry Potter",
              email: "-",
              username: "potter"
            }
          ]
        },
        {
          name: "Others",
          identities: [
            {
              uuid: "4ce562",
              name: "Harry Potter",
              email: "hpotter@example.net",
              username: "-",
              source: "gerrit"
            }
          ]
        }],
        enrollments: [
          {
            organization: {
              name: "Griffyndor",
              id: "2"
            },
            start: "1991-09-01",
            end: "1997-06-02T00:00:00+00:00"
          },
          {
            organization: {
              name: "Hogwarts School of Witchcraft and Wizardry",
              id: "1"
            },
            start: "1991-09-01",
            end: "1997-06-02T00:00:00+00:00"
          }
        ]
      },
      {
        id: 3,
        name: "Voldemort",
        organization: "Death Eaters",
        email: "",
        sources: [ "others" ],
        identities: [
        {
          name: "Others",
          identities: [
            {
              uuid: "4ce562",
              name: "-",
              email: "voldemort@example.net",
              username: "voldemort",
              source: "Jira"
            }
          ]
        }],
        enrollments: [
          {
            organization: {
              name: "Death Eaters",
              id: "1"
            },
            start: "1950-09-01",
            end: "1998-06-02T00:00:00+00:00"
          }
        ]
      },
      {
        id: 4,
        name: "Albus Dumbledore",
        organization: "Order of the Phoenix",
        email: "albus.dumbledore@example.com",
        sources: [ "gitlab", "others" ],
        identities: [
          {
            name: "GitLab",
            identities: [
              {
                uuid: "4ce562",
                name: "Albus Dumbledore",
                email: "headmaster@hogwarts.net",
                username: "albus",
                source: "GitLab"
              }
            ]
          },
        {
          name: "Others",
          identities: [
            {
              uuid: "4ce562",
              name: "Albus Dumbledore",
              email: "adumbledore@example.net",
              username: "albus",
              source: "Jira"
            },
            {
              uuid: "808b18",
              name: "Albus Dumbledore",
              email: "adumbledore@example.net",
              username: "albus",
              source: "irc"
            }
          ]
        }],
        enrollments: [
          {
            organization: {
              name: "Order of the Phoenix",
              id: "1"
            },
            start: "1970-09-01",
            end: "1981-06-02T00:00:00+00:00"
          },
          {
            organization: {
              name: "Hogwarts School of Witchcraft and Wizardry",
              id: "2"
            },
            start: "1892-09-01",
            end: "1899-06-02T00:00:00+00:00"
          },
          {
            organization: {
              name: "Griffyndor House",
              id: "3"
            },
            start: "1892-09-01T00:00:00+00:00",
            end: "1997-05-02T00:00:00+00:00"
          }
        ]
      },
      {
        id: 5,
        name: "Hagrid",
        organization: "",
        email: "hagrid@example.com",
        sources: [ "git" ],
        identities: [
          {
            name: "Git",
            identities: [
              {
                uuid: "4ce562",
                name: "hagrid",
                email: "hagrid@example.com",
                username: "hagrid"
              }
            ]
          },
        ],
        enrollments: []
      }
    ]
  })
});
