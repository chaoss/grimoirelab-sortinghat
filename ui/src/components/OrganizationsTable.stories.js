import { storiesOf } from "@storybook/vue";

import OrganizationsTable from "./OrganizationsTable.vue";

export default {
  title: "OrganizationsTable",
  excludeStories: /.*Data$/
};

const OrganizationsTableTemplate = '<organizations-table :fetch-page="getOrganizations.bind(this)" />';

export const Default = () => ({
  components: { OrganizationsTable },
  template: OrganizationsTableTemplate,
  methods: {
    getOrganizations(page) {
      return this.query[page - 1];
    }
  },
  data: () => ({
    query: [
      {
        data: {
          organizations: {
            entities: [
              {
                name: "Griffyndor",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 },
                  { id: 4 },
                  { id: 5 }
                ]
              },
              {
                name: "Slytherin",
                enrollments: [
                  { id: 1 },
                  { id: 2 }
                ]
              },
              {
                name: "Ravenclaw",
                enrollments: [
                  { id: 1 },
                  { id: 2 },
                  { id: 3 }
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
                  name: "Hufflepuff",
                  enrollments: [
                    { id: 1 },
                    { id: 2 },
                    { id: 3 },
                    { id: 4 }
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
