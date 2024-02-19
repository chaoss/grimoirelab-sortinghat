import OrganizationsTable from "./OrganizationsTable.vue";

export default {
  title: "OrganizationsTable",
  excludeStories: /.*Data$/,
};

const OrganizationsTableTemplate = `
  <organizations-table
    :is-group="isGroup"
    :name="name"
    :fetch-page="getOrganizations.bind(this)"
    :enroll="enroll"
    :add-organization="addOrganization.bind(this)"
    :add-domain="addDomain"
    :delete-domain="deleteDomain"
    :delete-organization="deleteOrganization"
    :add-team="addTeam"
    :delete-team="deleteTeam"
    :fetch-teams="fetchTeams"
    :add-alias="() => {}"
    :delete-alias="() => {}"
  />
`;

export const Organizations = () => ({
  components: { OrganizationsTable },
  template: OrganizationsTableTemplate,
  methods: {
    getOrganizations(page, items, filters) {
      const results = JSON.parse(JSON.stringify(this.query[page - 1]));
      if (filters.term) {
        results.data.organizations.entities =
          results.data.organizations.entities.filter((organization) =>
            organization.name.toUpperCase().includes(filters.term.toUpperCase())
          );
        results.data.organizations.pageInfo.totalResults =
          results.data.organizations.entities.length;
      }
      return results.data.organizations;
    },
    enroll() {
      return true;
    },
    addOrganization(organization) {
      this.query[0].data.organizations.entities.push({
        id: organization,
        name: organization,
        enrollments: [],
        domains: [],
      });
      return true;
    },
    addDomain(domain, organization) {
      const index = this.query[0].data.organizations.entities.findIndex(
        (entity) => entity.name === organization
      );
      this.query[0].data.organizations.entities[index].domains.push({
        domain: domain,
      });
      return true;
    },
    deleteDomain(domain) {
      this.query[0].data.organizations.entities.find((entity) => {
        const index = entity.domains.findIndex(
          (item) => item.domain === domain
        );
        entity.domains.splice(index, 1);
      });
    },
    deleteOrganization(name) {
      const index = this.query[0].data.organizations.entities.findIndex(
        (entity) => entity.name === name
      );
      this.query[0].data.organizations.entities.splice(index, 1);
    },
    addTeam() {
      return;
    },
    deleteTeam() {
      return;
    },
    fetchTeams() {
      return {
        data: {
          teams: {
            entities: [],
          },
        },
      };
    },
  },
  data: () => ({
    query: [
      {
        data: {
          organizations: {
            entities: [
              {
                id: 1,
                name: "Griffyndor",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                  { id: 4 },
                  { id: 5 },
                ],
                domains: [{ domain: "griffyndor.hogwarts.edu" }],
                aliases: [{ alias: "Griffyndor House" }],
              },
              {
                id: 2,
                name: "Slytherin",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                ],
                domains: [{ domain: "slytherin.hogwarts.edu" }],
                aliases: [{ alias: "Slytherin House" }],
              },
              {
                id: 3,
                name: "Ravenclaw",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                ],
                domains: [{ domain: "ravenclaw.hogwarts.edu" }],
                aliases: [{ alias: "Ravenclaw House" }],
              },
            ],
            pageInfo: {
              page: 1,
              pageSize: 3,
              numPages: 2,
              totalResults: 4,
            },
          },
        },
      },
      {
        data: {
          organizations: {
            entities: [
              {
                id: 4,
                name: "Hufflepuff",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                  { id: 4 },
                ],
                domains: [{ domain: "hufflepuff.hogwarts.edu" }],
              },
            ],
            pageInfo: {
              page: 2,
              pageSize: 3,
              numPages: 2,
              totalResults: 4,
            },
          },
        },
      },
    ],
    isGroup: false,
    name: "Organizations",
  }),
});

export const Groups = () => ({
  components: { OrganizationsTable },
  template: OrganizationsTableTemplate,
  methods: {
    getOrganizations(page, items, filters) {
      const results = JSON.parse(JSON.stringify(this.query[page - 1]));
      if (filters.term) {
        results.data.organizations.entities =
          results.data.organizations.entities.filter((organization) =>
            organization.name.toUpperCase().includes(filters.term.toUpperCase())
          );
        results.data.organizations.pageInfo.totalResults =
          results.data.organizations.entities.length;
      }
      return results.data.organizations;
    },
    enroll() {
      return true;
    },
    addOrganization(organization) {
      this.query[0].data.organizations.entities.push({
        id: organization,
        name: organization,
        enrollments: [],
        domains: [],
      });
      return true;
    },
    addDomain(domain, organization) {
      const index = this.query[0].data.organizations.entities.findIndex(
        (entity) => entity.name === organization
      );
      this.query[0].data.organizations.entities[index].domains.push({
        domain: domain,
      });
      return true;
    },
    deleteDomain(domain) {
      this.query[0].data.organizations.entities.find((entity) => {
        const index = entity.domains.findIndex(
          (item) => item.domain === domain
        );
        entity.domains.splice(index, 1);
      });
    },
    deleteOrganization(name) {
      const index = this.query[0].data.organizations.entities.findIndex(
        (entity) => entity.name === name
      );
      this.query[0].data.organizations.entities.splice(index, 1);
    },
    addTeam() {
      return;
    },
    deleteTeam() {
      return;
    },
    fetchTeams() {
      return {
        data: {
          teams: {
            entities: [],
          },
        },
      };
    },
  },
  data: () => ({
    query: [
      {
        data: {
          organizations: {
            entities: [
              {
                id: 1,
                name: "Dark Force Defence League",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                  { id: 4 },
                  { id: 5 },
                ],
              },
              {
                id: 2,
                name: "Extraordinary Society of Potioneers",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                ],
              },
              {
                id: 3,
                name: "Society for the Tolerance of Vampires",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                ],
              },
            ],
            pageInfo: {
              page: 1,
              pageSize: 3,
              numPages: 2,
              totalResults: 5,
            },
          },
        },
      },
      {
        data: {
          organizations: {
            entities: [
              {
                id: 4,
                name: "Frog Choir",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                  { id: 4 },
                ],
              },
              {
                id: 5,
                name: "Celestial Ball decorating committee",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                ],
              },
              {
                id: 6,
                name: "Duelling Club",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                ],
              },
            ],
            pageInfo: {
              page: 2,
              pageSize: 3,
              numPages: 2,
              totalResults: 5,
            },
          },
        },
      },
    ],
    isGroup: true,
    name: "Groups",
  }),
});
