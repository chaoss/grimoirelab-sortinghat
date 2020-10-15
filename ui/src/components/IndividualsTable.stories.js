import { storiesOf } from "@storybook/vue";

import IndividualsTable from "./IndividualsTable.vue";

export default {
  title: "IndividualsTable",
  excludeStories: /.*Data$/
};

const IndividualsTableTemplate = `
  <individuals-table
    :fetch-page="queryIndividuals.bind(this)"
    :delete-item="deleteIndividual"
    :merge-items="deleteIndividual"
  />
`;

export const Default = () => ({
  components: { IndividualsTable },
  template: IndividualsTableTemplate,
  methods: {
    queryIndividuals(page) {
      return this.query[page - 1];
    },
    deleteIndividual() {
      return true;
    }
  },
  data: () => ({
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
                    uuid: "03b3428ee1",
                    username: "triddle"
                  },
                  {
                    uuid: "808b182",
                    name: "Voldemort",
                    email: "-",
                    username: "voldemort",
                    source: "github"
                  },
                  {
                    uuid: "006afa3",
                    name: "Tom Marvolo Riddle",
                    email: "triddle@example.net",
                    username: "triddle",
                    source: "git"
                  },
                  {
                    uuid: "abce324",
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
                    uuid: "03b3428ee5",
                    username: "-"
                  },
                  {
                    uuid: "4ce5626",
                    name: "H. Potter",
                    email: "hpotter@example.net",
                    username: "potter",
                    source: "git"
                  },
                  {
                    uuid: "4ce5627",
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
                    uuid: "4ce5628",
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
                    uuid: "4ce5659",
                    name: "Ron Weasley",
                    email: "rweasley@example.net",
                    username: "",
                    source: "git"
                  },
                  {
                    uuid: "4ce56210",
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
                    uuid: "4ce56211",
                    name: "Hermione Granger",
                    email: "hgranger@example.net",
                    username: "hermione",
                    source: "gitlab"
                  },
                  {
                    uuid: "4ce56212",
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
              numPages: 2,
              totalResults: 7
            }
          }
        }
      },
      {
        data: {
          individuals: {
            entities: [
              {
                isLocked: false,
                profile: {
                  name: "Albus Dumbledore",
                  id: "6",
                  email: "albus.dumbledore@example.com",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "4ce562",
                    name: "Albus Dumbledore",
                    email: "headmaster@hogwarts.net",
                    username: "albus",
                    source: "GitLab"
                  },
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
                ],
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
                isLocked: false,
                profile: {
                  name: "Hagrid",
                  id: "7",
                  email: "hagrid@example.com",
                  isBot: false
                },
                identities: [
                  {
                    uuid: "4ce562",
                    name: "hagrid",
                    email: "hagrid@example.com",
                    username: "hagrid",
                    source: "Git"
                  }
                ],
                enrollments: []
              }
            ],
            pageInfo: {
              page: 2,
              pageSize: 5,
              numPages: 2,
              totalResults: 7
            }
          }
        }
      }
    ]
  })
});
