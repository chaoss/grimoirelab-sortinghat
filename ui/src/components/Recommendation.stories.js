import Recommendations from "./Recommendations.vue";

export default {
  title: "Recommendations",
  excludeStories: /.*Data$/
};

const defaultTemplate = `
<div>
  <recommendations :items="items" :merge-items="merge" />
</div>`;

const slotTemplate = `
<div>
  <recommendations :items="items" :merge-items="merge">
    <template v-slot:activator="{ on, items }">
      <v-chip
        v-on="on"
        color="primary"
        text-color="white"
      >
        <v-avatar left>
          <v-icon>mdi-hexagram</v-icon>
        </v-avatar>
        Click to open modal
      </v-chip>
    </template>
  </recommendations>
</div>`;

const items = [
  {
    from: {
      name: "Tom Marvolo Riddle",
      uuid: "164e41c60c23",
      id: "1",
      email: "triddle@example.com",
      isBot: false,
      isLocked: false,
      sources: [
        { name: "git", icon: "mdi-git" },
        { name: "gitlab", icon: "mdi-gitlab" }
      ],
      identities: [
        {
          name: "GitLab",
          icon: "mdi-gitlab",
          identities: [
            {
              name: "Tom Marvolo Riddle",
              source: "GitLab",
              email: "triddle@example.net",
              username: "triddle"
            }
          ]
        },
        {
          name: "git",
          icon: "mdi-git",
          identities: [
            {
              name: "Tom Marvolo Riddle",
              email: "triddle@example.net",
              source: "git"
            },
            {
              name: "Tom Marvolo Riddle",
              email: "voldemort@example.net",
              source: "git"
            }
          ]
        }
      ],
      enrollments: [
        {
          group: { name: "Hogwarts" },
          start: "1938-09-01",
          end: "1945-06-02T00:00:00+00:00"
        }
      ]
    },
    to: {
      name: "Voldemort",
      uuid: "164e41c60c23",
      email: "triddle@example.com",
      isBot: false,
      isLocked: false,
      sources: [
        { name: "git", icon: "mdi-git" },
        { name: "github", icon: "mdi-github" }
      ],
      identities: [
        {
          name: "GitHub",
          icon: "mdi-github",
          identities: [
            {
              name: "Voldemort",
              username: "voldemort",
              source: "github"
            }
          ]
        },
        {
          name: "git",
          icon: "mdi-git",
          identities: [
            {
              name: "voldemort",
              email: "voldemort@example.net",
              source: "git"
            }
          ]
        }
      ],
      enrollments: [
        {
          group: { name: "Slytherin" },
          start: "1938-09-01T00:00:00+00:00",
          end: "1998-05-02T00:00:00+00:00"
        }
      ]
    }
  },
  {
    from: {
      name: "Dumbledore",
      uuid: "164e41c60c25",
      email: "albus.dumbledore@example.com",
      isBot: false,
      isLocked: false,
      sources: [{ name: "git", icon: "mdi-git" }],
      identities: [
        {
          name: "git",
          icon: "mdi-git",
          identities: [
            {
              name: "Dumbledore",
              email: "albus.dumbledore@example.com",
              source: "git"
            }
          ]
        }
      ],
      enrollments: []
    },
    to: {
      name: "Albus Dumbledore",
      uuid: "164e41c60c26",
      email: "albus.dumbledore@example.com",
      isBot: false,
      isLocked: false,
      sources: [
        { name: "gitlab", icon: "mdi-gitlab" },
        { name: "jira", icon: "mdi-jira" },
        { name: "other sources", icon: "mdi-account-multiple" }
      ],
      identities: [
        {
          name: "gitlab",
          icon: "mdi-gitlab",
          identities: [
            {
              uuid: "1",
              name: "Albus Dumbledore",
              email: "headmaster@hogwarts.net",
              username: "albus",
              source: "GitLab"
            }
          ]
        },
        {
          name: "jira",
          icon: "mdi-jira",
          identities: [
            {
              uuid: "2",
              name: "Albus Dumbledore",
              email: "adumbledore@example.net",
              username: "albus",
              source: "Jira"
            }
          ]
        },
        {
          name: "other sources",
          icon: "mdi-account-multiple",
          identities: [
            {
              uuid: "3",
              name: "Albus Dumbledore",
              username: "albus",
              source: "irc"
            }
          ]
        }
      ],
      enrollments: [
        {
          group: { name: "Order of the Phoenix" },
          start: "1970-09-01",
          end: "1981-06-02T00:00:00+00:00"
        },
        {
          group: { name: "Hogwarts School of Witchcraft and Wizardry" },
          start: "1892-09-01",
          end: "1899-06-02T00:00:00+00:00"
        }
      ]
    }
  }
];

export const Default = () => ({
  components: { Recommendations },
  template: defaultTemplate,
  methods: {
    merge() {
      return { data: { merge: true } };
    }
  },
  data: () => ({
    items: items
  })
});

export const CustomModalActivator = () => ({
  components: { Recommendations },
  template: slotTemplate,
  methods: {
    merge() {
      return { data: { merge: true } };
    }
  },
  data: () => ({
    items: items
  })
});

export const ErrorOnMerge = () => ({
  components: { Recommendations },
  template: defaultTemplate,
  methods: {
    merge() {
      throw "Error merging individuals"
    }
  },
  data: () => ({
    items: items
  })
});
