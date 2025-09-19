import Recommendations from "./Recommendations.vue";

export default {
  title: "Recommendations",
  excludeStories: /.*Data$/,
};

const defaultTemplate = `
<v-layout>
  <recommendations />
</v-layout>`;

const slotTemplate = `
<v-layout>
  <recommendations>
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
</v-layout>`;

const recommendations = [
  {
    data: {
      recommendedMerge: {
        entities: [
          {
            id: "38",
            individual1: {
              mk: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
              isLocked: false,
              profile: {
                name: "Tom Marvolo Riddle",
                id: "1",
                email: "triddle@example.com",
              },
              identities: [
                {
                  name: "Tom Marvolo Riddle",
                  source: "git",
                  email: "triddle@example.com",
                  uuid: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
                },
              ],
              enrollments: [
                {
                  group: { name: "Hogwarts" },
                  start: "1938-09-01",
                  end: "1945-06-02T00:00:00+00:00",
                },
              ],
              matchRecommendationSet: [
                {
                  id: 39,
                  individual: {
                    mk: "8998b2f0bd86780fb7c8c141956d68c9628cbec8",
                    isLocked: false,
                    profile: {
                      name: "Voldemort",
                      id: "37",
                      email: "triddle@example.com",
                      isBot: false,
                    },
                    identities: [
                      {
                        name: "Voldemort",
                        source: "git",
                        email: "triddle@example.com",
                        uuid: "8998b2f0bd86780fb7c8c141956d68c9628cbec8",
                      },
                      {
                        username: "voldemort",
                        source: "github",
                        email: "triddle@example.com",
                        uuid: "8998b2f0bd86780fb7c8c141956d68c9628cbec9",
                      },
                    ],
                    enrollments: [],
                  },
                },
                {
                  id: 40,
                  individual: {
                    mk: "8998b2f0bd86780fb7c8c141956d68c9628cbec8",
                    isLocked: false,
                    profile: {
                      name: "T. Riddle",
                      id: "37",
                      email: "triddle@example.com",
                      isBot: false,
                    },
                    identities: [
                      {
                        source: "git",
                        email: "triddle@example.com",
                        uuid: "8998b2f0bd86780fb7c8c141956d68c9628cbec9",
                      },
                    ],
                    enrollments: [],
                  },
                },
              ],
            },
          },
        ],
        pageInfo: {
          totalResults: 4,
          page: 1,
          hasNext: true,
        },
      },
    },
  },
  {
    data: {
      recommendedMerge: {
        entities: [
          {
            id: "38",
            individual1: {
              mk: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
              isLocked: false,
              profile: {
                name: "Albus Dumbledore",
                id: "1",
                email: "albus.dumbledore@example.com",
              },
              identities: [
                {
                  name: "Albus Dumbledore",
                  source: "gitlab",
                  email: "headmaster@hogwarts.net",
                  username: "dumbledore",
                  uuid: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
                },
                {
                  name: "Albus Dumbledore",
                  source: "jira",
                  email: "dumbledore@example.net",
                  username: "albus",
                  uuid: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
                },
              ],
              enrollments: [
                {
                  group: { name: "Order of the Phoenix" },
                  start: "1970-09-01",
                  end: "1981-06-02T00:00:00+00:00",
                },
                {
                  group: { name: "Hogwarts School of Witchcraft and Wizardry" },
                  start: "1892-09-01",
                  end: "1899-06-02T00:00:00+00:00",
                },
              ],
              matchRecommendationSet: [
                {
                  id: 39,
                  individual: {
                    mk: "8998b2f0bd86780fb7c8c141956d68c9628cbec8",
                    isLocked: false,
                    profile: {
                      id: "37",
                      email: "dumbledore@example.net",
                      isBot: false,
                    },
                    identities: [
                      {
                        source: "git",
                        email: "dumbledore@example.net",
                        uuid: "4350d4c5916cfe8e2e18d290e02a471d95b112d7",
                      },
                    ],
                    enrollments: [],
                  },
                },
              ],
            },
          },
        ],
        pageInfo: {
          totalResults: 1,
          page: 2,
          hasNext: false,
        },
      },
    },
  },
];

export const Default = () => ({
  components: { Recommendations },
  template: defaultTemplate,
  data() {
    return {
      index: 0,
    };
  },
  methods: {
    getRecommendations() {
      return recommendations[this.index];
    },
    manageRecommendation() {
      if (recommendations.length > 1) {
        recommendations.shift();
      }
      return true;
    },
  },
  provide() {
    return {
      getRecommendationsCount: this.getRecommendations,
      getRecommendations: this.getRecommendations,
      manageRecommendation: this.manageRecommendation,
      deleteMergeRecommendations: () => {},
    };
  },
});

export const CustomModalActivator = () => ({
  components: { Recommendations },
  template: slotTemplate,
  data() {
    return {
      index: 0,
    };
  },
  methods: {
    getRecommendations() {
      return recommendations[this.index];
    },
    manageRecommendation() {
      this.index = +!this.index;
      return true;
    },
    deleteRecommendations() {
      return true;
    },
  },
  provide() {
    return {
      getRecommendationsCount: this.getRecommendations,
      getRecommendations: this.getRecommendations,
      manageRecommendation: this.manageRecommendation,
      deleteMergeRecommendations: () => {},
    };
  },
});
