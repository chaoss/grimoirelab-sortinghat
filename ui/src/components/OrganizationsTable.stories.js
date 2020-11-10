import { storiesOf } from "@storybook/vue";

import OrganizationsTable from "./OrganizationsTable.vue";

export default {
  title: "OrganizationsTable",
  excludeStories: /.*Data$/
};

const OrganizationsTableTemplate = `
  <organizations-table
    :fetch-page="getOrganizations.bind(this)"
    :enroll="enroll"
    :add-organization="addOrganization.bind(this)"
    :add-domain="addDomain"
  />
`;

export const Default = () => ({
  components: { OrganizationsTable },
  template: OrganizationsTableTemplate,
  methods: {
    getOrganizations(page) {
      return this.query[page - 1];
    },
    enroll() {
      return true;
    },
    addOrganization(organization) {
      this.query[0].data.organizations.entities.push({
        id: organization,
        name: organization,
        enrollments: [],
        domains: []
      });
      return true;
    },
    addDomain(domain, organization) {
      const index = this.query[0].data.organizations.entities.findIndex(
        entity => entity.name === organization
      );
      this.query[0].data.organizations.entities[index].domains.push({
        domain: domain
      });
      return true;
    }
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
                  { id: 5 }
                ],
                domains: [
                  { domain: "griffyndor.hogwarts.edu" }
                ]
              },
              {
                id: 2,
                name: "Slytherin",
                enrollments: [
                  { id: 1 },
                  { id: 2 }
                ],
                domains: [
                  { domain: "slytherin.hogwarts.edu" }
                ]
              },
              {
                id: 3,
                name: "Ravenclaw",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 }
                ],
                domains: [
                  { domain: "ravenclaw.hogwarts.edu" }
                ]
              },
              ],
              pageInfo: {
                page: 1,
                pageSize: 3,
                numPages: 2,
                totalResults: 4
              }
            }
          }
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
                    { id: 4 }
                  ],
                  domains: [
                    { domain: "hufflepuff.hogwarts.edu" }
                  ]
                },
                ],
                pageInfo: {
                  page: 2,
                  pageSize: 3,
                  numPages: 2,
                  totalResults: 4
                }
              }
            }
          }
      ]
  })
});
