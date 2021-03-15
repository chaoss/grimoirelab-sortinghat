import ExpandedIndividual from "./ExpandedIndividual.vue";

export default {
  title: "ExpandedIndividual",
  excludeStories: /.*Data$/
};

const expandedIndividualTemplate = `
  <expanded-individual
    :enrollments="enrollments"
    :identities="identities"
    :compact="compact"
    :uuid="uuid"
    :get-countries="getCountries.bind(this)"
  />`;

export const Default = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
    compact: false,
    name: "Tom Marvolo Riddle",
    countries: [
      { code: "AD", name: "Andorra" },
      { code: "AE", name: "United Arab Emirates" },
      { code: "AF", name: "Afghanistan" },
      { code: "AG", name: "Antigua and Barbuda" },
      { code: "AI", name: "Anguilla" },
      { code: "AL", name: "Albania" },
      { code: "AM", name: "Armenia" }
    ],
    identities: [
      {
        name: "GitHub",
        icon: "mdi-github",
        identities: [
          {
            uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
            name: "Tom Marvolo Riddle",
            email: "triddle@example.net",
            username: "triddle",
            source: "GitHub"
          },
          {
            uuid: "164e41c60c28698ac30b0d17176d3e720e036918",
            name: "Voldemort",
            email: "-",
            username: "voldemort",
            source: "GitHub"
          }
        ]
      },
      {
        name: "Git",
        icon: "mdi-git",
        identities: [
          {
            uuid: "10982379421b80e13266db011d6e5131dd519016",
            name: "voldemort",
            email: "voldemort@example.net",
            username: "-",
            source: "git"
          }
        ]
      },
      {
        name: "Others",
        icon: "mdi-account-multiple",
        identities: [
          {
            uuid: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
            name: "-",
            email: "-",
            username: "voldemort",
            source: "irc"
          }
        ]
      }
    ],
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
  }),
  methods: {
    getCountries() {
      return this.countries;
    }
  }
});

export const Compact = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    uuid: "006afa",
    compact: true,
    name: "Tom Marvolo Riddle",
    identities: [
      {
        name: "GitHub",
        icon: "mdi-github",
        identities: [
          {
            uuid: "006afa",
            name: "Tom Marvolo Riddle",
            email: "triddle@example.net",
            username: "triddle",
            source: "GitHub"
          },
          {
            uuid: "808b18",
            name: "Voldemort",
            email: "-",
            username: "voldemort",
            source: "GitHub"
          }
        ]
      },
      {
        name: "Git",
        icon: "mdi-git",
        identities: [
          {
            uuid: "abce32",
            name: "voldemort",
            email: "voldemort@example.net",
            username: "-",
            source: "git"
          }
        ]
      },
      {
        name: "Others",
        icon: "mdi-account-multiple",
        identities: [
          {
            uuid: "4ce562",
            name: "-",
            email: "-",
            username: "voldemort",
            source: "irc"
          }
        ]
      }
    ],
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
  }),
  methods: {
    getCountries() {
      return true;
    }
  }
});

export const NoOrganizations = () => ({
  components: { ExpandedIndividual },
  template: expandedIndividualTemplate,
  data: () => ({
    uuid: "164e41c60c28698ac30b0d17176d3e720e036918",
    compact: false,
    identities: [
      {
        name: "Git",
        icon: "mdi-github",
        identities: [
          {
            uuid: "164e41c60c28698ac30b0d17176d3e720e036918",
            name: "Hagrid",
            email: "hagrid@example.com",
            username: "hagrid"
          }
        ]
      }
    ],
    enrollments: [],
    countries: [
      { code: "AD", name: "Andorra" },
      { code: "AE", name: "United Arab Emirates" },
      { code: "AF", name: "Afghanistan" },
      { code: "AG", name: "Antigua and Barbuda" },
      { code: "AI", name: "Anguilla" },
      { code: "AL", name: "Albania" },
      { code: "AM", name: "Armenia" }
    ]
  }),
  methods: {
    getCountries() {
      return this.countries;
    }
  }
});
