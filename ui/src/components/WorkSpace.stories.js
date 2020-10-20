import { storiesOf } from "@storybook/vue";

import WorkSpace from "./WorkSpace.vue";
import IndividualsTable from "./IndividualsTable.vue";

export default {
  title: "WorkSpace",
  excludeStories: /.*Data$/
};

const workSpaceTemplate =
  '<work-space :individuals="individuals" :merge-items="mergeItems"/>';

const dragAndDropTemplate = `
  <div>
  <work-space :individuals="individuals" :merge-items="mergeItems"/>
  <individuals-table :fetch-page="queryIndividuals.bind(this)" :delete-item="deleteItem" :merge-items="deleteItem" />
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
        sources: ["gitlab", "GitHub", "git"],
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
        sources: ["GitHub", "git", "others"],
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
    }
  }
});

export const DragAndDrop = () => ({
  components: { WorkSpace, IndividualsTable },
  template: dragAndDropTemplate,
  methods: {
    queryIndividuals(page) {
      return this.query[page - 1];
    },
    mergeItems() {
      this.individuals = [this.individuals.shift()];
    }
  },
  data: () => ({
    individuals: [],
    deleteItem: () => {},
    query: [
      {
        data: {
          individuals: {
            entities: [
              {
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
                    uuid: "03b3428ee",
                    username: "triddle"
                  },
                  {
                    uuid: "808b18",
                    name: "Voldemort",
                    email: "-",
                    username: "voldemort",
                    source: "github"
                  },
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
                    uuid: "03b3428ee",
                    username: "-"
                  },
                  {
                    uuid: "4ce562",
                    name: "H. Potter",
                    email: "hpotter@example.net",
                    username: "potter",
                    source: "git"
                  },
                  {
                    uuid: "4ce562",
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
                isLocked: true,
                profile: {
                  name: "Voldemort",
                  id: "3",
                  email: "",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "4ce562",
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
                isLocked: false,
                profile: {
                  name: "Ron Weasley",
                  id: "4",
                  email: "rweasley@example.com",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "4ce565",
                    name: "Ron Weasley",
                    email: "rweasley@example.net",
                    username: "",
                    source: "git"
                  },
                  {
                    uuid: "4ce562",
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
                isLocked: false,
                profile: {
                  name: "Hermione Granger",
                  id: "5",
                  email: "hgranger@example.com",
                  isBot: true
                },
                identities: [
                  {
                    uuid: "4ce562",
                    name: "Hermione Granger",
                    email: "hgranger@example.net",
                    username: "hermione",
                    source: "gitlab"
                  },
                  {
                    uuid: "4ce562",
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
    ]
  })
})
