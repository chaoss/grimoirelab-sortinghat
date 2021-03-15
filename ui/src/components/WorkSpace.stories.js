import WorkSpace from "./WorkSpace.vue";
import IndividualsTable from "./IndividualsTable.vue";

export default {
  title: "WorkSpace",
  excludeStories: /.*Data$/
};

const workSpaceTemplate =
  '<work-space :individuals="individuals" :merge-items="mergeItems" :move-item="moveItem" :enroll="() => {}"/>';

const dragAndDropTemplate = `
  <div>
  <work-space
    :individuals="individuals"
    :merge-items="mergeItems"
    :move-item="moveItem"
    :highlight-individual="highlightInWorkspace"
    :enroll="deleteItem"
    @highlight="highlightIndividual($event, 'highlightInTable', true)"
    @stopHighlight="highlightIndividual($event, 'highlightInTable', false)"
    @deselect="deselectIndividuals"
  />
  <individuals-table
    :fetch-page="queryIndividuals.bind(this)"
    :delete-item="deleteItem"
    :merge-items="deleteItem"
    :unmerge-items="deleteItem"
    :move-item="moveItem"
    :highlight-individual="highlightInTable"
    :add-identity="deleteItem"
    :enroll="deleteItem"
    :update-profile="deleteItem"
    :get-countries="getCountries.bind(this)"
    :lock-individual="deleteItem"
    :unlock-individual="deleteItem"
    :withdraw="deleteItem"
    :update-enrollment="deleteItem"
    @highlight="highlightIndividual($event, 'highlightInWorkspace', true)"
    @stopHighlight="highlightIndividual($event, 'highlightInWorkspace', false)"
    ref="table"
  />
  </div>
`;

export const Default = () => ({
  components: { WorkSpace },
  template: workSpaceTemplate,
  data: () => ({
    individuals: [
      {
        name: "Tom Marvolo Riddle",
        uuid: "164e41c60c23",
        id: "1",
        email: "triddle@example.com",
        isBot: false,
        isLocked: false,
        organization: "Slytherin",
        isSelected: false,
        sources: [
          { name: "git", icon: "mdi-git" },
          { name: "github", icon: "mdi-github" },
          { name: "gitlab", icon: "mdi-gitlab" }
        ],
        identities: [
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
      },
      {
        name: "Harry Potter",
        uuid: "164e41c60c28",
        id: "2",
        email: "hpotter@example.com",
        isLocked: false,
        isSelected: false,
        organization: "Griffyndor",
        sources: [
          { name: "git", icon: "mdi-git" },
          { name: "github", icon: "mdi-github" },
          { name: "Other sources", icon: "mdi-account-multiple" }
        ],
        identities: [
          {
            name: "GitHub",
            identities: [
              {
                name: "Harry Potter",
                source: "GitHub",
                email: "hpotter@example.net",
                uuid: "03b3428ee",
                username: "-"
              }
            ]
          },
          {
            name: "git",
            identities: [
              {
                uuid: "4ce562",
                name: "H. Potter",
                email: "hpotter@example.net",
                username: "potter",
                source: "git"
              }
            ]
          },
          {
            name: "others",
            identities: [
              {
                uuid: "4ce562",
                name: "Harry Potter",
                email: "hpotter@example.net",
                username: "-",
                source: "gerrit"
              }
            ]
          }
        ],
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
      }
    ]
  }),
  methods: {
    mergeItems() {
      this.individuals.pop();
    },
    moveItem() {
      return true;
    }
  }
});

export const Empty = () => ({
  components: { WorkSpace },
  template: workSpaceTemplate,
  data: () => ({
    individuals: []
  }),
  methods: {
    mergeItems() {
      this.individuals.pop();
    },
    moveItem() {
      return true;
    }
  }
});

export const DragAndDrop = () => ({
  components: { WorkSpace, IndividualsTable },
  template: dragAndDropTemplate,
  methods: {
    queryIndividuals(page, items, filters) {
      const results = JSON.parse(JSON.stringify(this.query[page - 1]));
      if (filters.term) {
        results.data.individuals.entities = results.data.individuals.entities.filter(
          individual =>
            individual.profile.name
              .toUpperCase()
              .includes(filters.term.toUpperCase())
        );
        results.data.individuals.pageInfo.totalResults =
          results.data.individuals.entities.length;
      }
      return results;
    },
    mergeItems() {
      this.individuals = [this.individuals.shift()];
    },
    highlightIndividual(individual, component, highlight) {
      this[component] = highlight ? individual.uuid : undefined;
    },
    moveItem() {
      return true;
    },
    deselectIndividuals() {
      this.$refs.table.deselectIndividuals();
    },
    getCountries() {
      return this.countries;
    }
  },
  data: () => ({
    individuals: [],
    highlightInTable: undefined,
    highlightInWorkspace: undefined,
    deleteItem: () => {},
    query: [
      {
        data: {
          individuals: {
            entities: [
              {
                mk: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
                isLocked: false,
                profile: {
                  name: "Tom Marvolo Riddle",
                  id: "1",
                  email: "triddle@example.com",
                  isBot: false
                },
                identities: [
                  {
                    name: "Tom Marvolo Riddle",
                    source: "GitLab",
                    email: "triddle@example.net",
                    uuid: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
                    username: "triddle"
                  },
                  {
                    uuid: "33697bad47122a2093d9edbbe179a72298971fd1",
                    name: "Voldemort",
                    email: "-",
                    username: "voldemort",
                    source: "github"
                  },
                  {
                    uuid: "e5ad332e1c29f907ebd10aeac6b757f501786b69",
                    name: "Tom Marvolo Riddle",
                    email: "triddle@example.net",
                    username: "triddle",
                    source: "git"
                  },
                  {
                    uuid: "10982379421b80e13266db011d6e5131dd519016",
                    name: "voldemort",
                    email: "voldemort@example.net",
                    username: "-",
                    source: "git"
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
              },
              {
                mk: "164e41c60c28698ac30b0d17176d3e720e036918",
                isLocked: false,
                profile: {
                  name: "Harry Potter",
                  id: "2",
                  email: "hpotter@example.com",
                  isBot: false
                },
                identities: [
                  {
                    name: "Harry Potter",
                    source: "GitHub",
                    email: "hpotter@example.net",
                    uuid: "164e41c60c28698ac30b0d17176d3e720e036918",
                    username: "-"
                  },
                  {
                    uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
                    name: "H. Potter",
                    email: "hpotter@example.net",
                    username: "potter",
                    source: "git"
                  },
                  {
                    uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
                    name: "Harry Potter",
                    email: "hpotter@example.net",
                    username: "-",
                    source: "gerrit"
                  }
                ],
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
                mk: "375458370ac0323bfb2e5a153e086551ef628d53",
                isLocked: true,
                profile: {
                  name: "Voldemort",
                  id: "3",
                  email: "",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
                    name: "-",
                    email: "voldemort@example.net",
                    username: "voldemort",
                    source: "Jira"
                  }
                ],
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
                mk: "66bc656d28a1522b650d537c9142be2e5c9e3b55",
                isLocked: false,
                profile: {
                  name: "Ron Weasley",
                  id: "4",
                  email: "rweasley@example.com",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "66bc656d28a1522b650d537c9142be2e5c9e3b55",
                    name: "Ron Weasley",
                    email: "rweasley@example.net",
                    username: "",
                    source: "git"
                  },
                  {
                    uuid: "85cffeb0ae25e2b36e1acec1b79a2219c9f057ce",
                    name: "Ron Weasley",
                    email: "ron@example.net",
                    username: "ronweasley",
                    source: "git"
                  }
                ],
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
                mk: "e4135c5c747dc69262cd4120a5c5ee51d07a9904",
                isLocked: false,
                profile: {
                  name: "Hermione Granger",
                  id: "5",
                  email: "hgranger@example.com",
                  isBot: true
                },
                identities: [
                  {
                    uuid: "e4135c5c747dc69262cd4120a5c5ee51d07a9904",
                    name: "Hermione Granger",
                    email: "hgranger@example.net",
                    username: "hermione",
                    source: "gitlab"
                  },
                  {
                    uuid: "3db176be6859adac3a454c5377af81b1b7e3f8d8",
                    name: "Hermione Granger",
                    email: "hgranger@example.net",
                    username: "h.granger",
                    source: "gerrit"
                  }
                ],
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
              }
            ],
            pageInfo: {
              page: 1,
              pageSize: 5,
              numPages: 1,
              totalResults: 5
            }
          }
        }
      }
    ],
    countries: [
      { code: "AD", name: "Andorra" },
      { code: "AE", name: "United Arab Emirates" },
      { code: "AF", name: "Afghanistan" },
      { code: "AG", name: "Antigua and Barbuda" },
      { code: "AI", name: "Anguilla" },
      { code: "AL", name: "Albania" },
      { code: "AM", name: "Armenia" }
    ]
  })
});
