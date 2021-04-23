<template>
  <v-main>
    <jobs-table :get-jobs="getJobs" class="mt-md-6" />
  </v-main>
</template>

<script>
import { getJobs } from "../apollo/queries";
import JobsTable from "../components/JobsTable";

export default {
  name: "Jobs",
  components: { JobsTable },
  methods: {
    async getJobs(page, pageSize) {
      const response = await getJobs(this.$apollo, page, pageSize);
      return response;
    }
  }
};
</script>
