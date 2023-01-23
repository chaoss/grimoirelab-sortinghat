<template>
  <v-main>
    <jobs-table
      :get-jobs="getJobs"
      class="mt-md-6"
      @affiliate="affiliate"
      @genderize="genderize"
      @unify="unify"
      @recommendMatches="recommendMatches"
      ref="table"
    />
    <v-snackbar v-model="snackbar.isOpen" color="error" text>
      {{ snackbar.text }}
    </v-snackbar>
  </v-main>
</template>

<script>
import { getJobs } from "../apollo/queries";
import {
  affiliate,
  genderize,
  unify,
  recommendMatches,
} from "../apollo/mutations";
import JobsTable from "../components/JobsTable";

export default {
  name: "Jobs",
  components: { JobsTable },
  data() {
    return {
      snackbar: {
        isOpen: false,
        text: null,
      },
    };
  },
  methods: {
    async getJobs(page, pageSize) {
      const response = await getJobs(this.$apollo, page, pageSize);
      return response;
    },
    async affiliate() {
      try {
        await affiliate(this.$apollo);
        this.$refs.table.getPaginatedJobs();
      } catch (error) {
        this.snackbar = Object.assign(this.snackbar, {
          isOpen: true,
          text: error,
        });
      }
    },
    async genderize({ exclude, noStrictMatching }) {
      try {
        await genderize(this.$apollo, exclude, noStrictMatching);
        this.$refs.table.getPaginatedJobs();
      } catch (error) {
        this.snackbar = Object.assign(this.snackbar, {
          isOpen: true,
          text: error,
        });
      }
    },
    async unify({ criteria, exclude }) {
      try {
        await unify(this.$apollo, criteria, exclude);
        this.$refs.table.getPaginatedJobs();
      } catch (error) {
        this.snackbar = Object.assign(this.snackbar, {
          isOpen: true,
          text: error,
        });
      }
    },
    async recommendMatches({ criteria, exclude }) {
      try {
        await recommendMatches(this.$apollo, criteria, exclude);
        this.$refs.table.getPaginatedJobs();
      } catch (error) {
        this.snackbar = Object.assign(this.snackbar, {
          isOpen: true,
          text: error,
        });
      }
    },
  },
};
</script>
