import ExpandedOrganization from "./ExpandedOrganization.vue";

export default {
  title: "ExpandedOrganization",
  excludeStories: /.*Data$/
};

const ExpandedOrganizationTemplate = `
  <expanded-organization
    :domains="domains"
    :organization="organization"
    :is-group="isGroup"
    :add-team="addTeam"
    :delete-team="deleteTeam"
    :fetch-teams="fetchTeams"
  />`;

export const Default = () => ({
  components: { ExpandedOrganization },
  template: ExpandedOrganizationTemplate,
  data: () => ({
    isGroup: false,
    domains: [{ domain: "ministryofmagic.uk" }, { domain: "mom.com" }],
    organization: "Ministry of Magic",
    query: [
      {
        data: {
          teams: {
            entities: [
              {
                name: "Committee on Experimental Charms",
                numchild: 0
              },
              {
                name: "Department of Magical Law Enforcement",
                numchild: 2
              },
              {
                name: "Department of Magical Accidents and Catastrophes",
                numchild: 0
              },
              {
                name:
                  "Department for the Regulation and Control of Magical Creatures",
                numchild: 1
              },
              {
                name: "Auror Office",
                parent: "Department of Magical Law Enforcement",
                numchild: 0
              },
              {
                name: "Improper Use of Magic Office",
                parent: "Department of Magical Law Enforcement",
                numchild: 0
              },
              {
                name: "Beast Division",
                parent:
                  "Department for the Regulation and Control of Magical Creatures",
                numchild: 0
              }
            ]
          }
        }
      }
    ]
  }),
  methods: {
    fetchTeams(filters) {
      let data = [];
      if (Object.keys(filters).includes("parent")) {
        this.query[0].data.teams.entities.forEach(team => {
          if (team["parent"] === filters["parent"]) {
            data.push(team);
          }
        });
      } else {
        this.query[0].data.teams.entities.forEach(team => {
          if (team["parent"] === undefined) {
            data.push(team);
          }
        });
      }
      const resp = {
        data: {
          teams: {
            entities: data
          }
        }
      };
      return resp;
    },
    addTeam(team, organization, parent) {
      const insertData = {
        name: team
      };
      if (parent) {
        insertData["parent"] = parent;
      }
      this.query[0].data.teams.entities.push(insertData);
      return true;
    },
    deleteTeam(team, organization) {
      this.query[0].data.teams.entities = this.query[0].data.teams.entities.filter(
        elem => elem.name != team
      );
      return true;
    }
  }
});

export const Group = () => ({
  components: { ExpandedOrganization },
  template: ExpandedOrganizationTemplate,
  data: () => ({
    isGroup: true,
    organization: "Witch Weekly",
    domains: null,
    query: {
      data: {
        teams: {
          entities: [
            {
              name: "Witches' League",
              numchild: 0
            }
          ]
        }
      }
    }
  }),
  methods: {
    fetchTeams() {
      return this.query;
    },
    addTeam() {
      return;
    },
    deleteTeam() {
      return;
    }
  }
});

export const Empty = () => ({
  components: { ExpandedOrganization },
  template: ExpandedOrganizationTemplate,
  data: () => ({
    isGroup: false,
    domains: [],
    organization: "Hogwarts",
    query: [
      {
        data: {
          teams: {
            entities: []
          }
        }
      }
    ]
  }),
  methods: {
    fetchTeams(filters) {
      let data = [];
      if (Object.keys(filters).includes("parent")) {
        this.query[0].data.teams.entities.forEach(team => {
          if (team["parent"] === filters["parent"]) {
            data.push(team);
          }
        });
      } else {
        this.query[0].data.teams.entities.forEach(team => {
          if (team["parent"] === undefined) {
            data.push(team);
          }
        });
      }
      const resp = {
        data: {
          teams: {
            entities: data
          }
        }
      };

      return resp;
    },
    addTeam(team, organization, parent) {
      const insertData = {
        name: team
      };
      if (parent) {
        insertData["parent"] = parent;
      }
      this.query[0].data.teams.entities.push(insertData);
      return true;
    },
    deleteTeam(team, organization) {
      this.query[0].data.teams.entities = this.query[0].data.teams.entities.filter(
        elem => elem.name != team
      );
      return true;
    }
  }
});
