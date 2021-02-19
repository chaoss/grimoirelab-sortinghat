import { storiesOf } from "@storybook/vue";

import JobsTable from "./JobsTable.vue";

export default {
  title: "JobsTable",
  excludeStories: /.*Data$/
};

const JobsTableTemplate = `<jobs-table :get-jobs="getJobs.bind(this)" />`;

export const Default = () => ({
  components: { JobsTable },
  template: JobsTableTemplate,
  methods: {
    getJobs(page) {
      return this.query[page - 1];
    }
  },
  data: () => ({
    query: [
      {
        data: {
          jobs: {
            entities: [
              {
                jobId: "a60346ea-6fbe-4501-896b-c8433a6b958f",
                status: "finished",
                jobType: "recommend_affiliations"
              },
              {
                jobId: "7fb401f4-6fbe-4501-896b-c8433a6b958f",
                status: "finished",
                jobType: "recommend_affiliations"
              },
              {
                jobId: "c7dac2c6-b0c5-4898-b92a-dc149fa5f175",
                status: "scheduled",
                jobType: "affiliate"
              },
              {
                jobId: "8a1aeaff-8f8f-4e3f-912b-04775c83f4c1",
                status: "failed",
                jobType: "recommend_affiliations"
              },
              {
                jobId: "bc904fc6-c8a3-4271-a0eb-223c6524ea71",
                status: "started",
                jobType: "affiliate"
              }
            ],
            pageInfo: {
              page: 1,
              numPages: 2,
              totalResults: 8
            }
          }
        }
      },
      {
        data: {
          jobs: {
            entities: [
              {
                jobId: "929ff864-819e-4c4c-93ac-81883ef48fb3",
                status: "queued",
                jobType: "recommend_matches",
              },
              {
                jobId: "52d20b58-6bf4-4a42-bcb9-235605c55bff",
                status: "queued",
                jobType: "recommend_matches"
              },
              {
                jobId: "fac43571-0248-455b-b4fd-650211afb8b1",
                status: "queued",
                jobType: "unify"
              }
            ],
            pageInfo: {
              page: 2,
              numPages: 2,
              totalResults: 8
            }
          }
        }
      }
    ]
  })
});
export const Empty = () => ({
  components: { JobsTable },
  template: JobsTableTemplate,
  methods: {
    getJobs(page) {
      return this.query;
    }
  },
  data: () => ({
    query: {
      data: {
        jobs: {
          entities: [],
          pageInfo: {
            page: 1,
            numPages: 1,
            totalResults: 0
          }}}}
  })
});
