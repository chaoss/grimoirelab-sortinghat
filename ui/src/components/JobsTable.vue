<template>
  <v-container class="jobs section mb-5 pa-0">
    <header class="header">
      <h4 class="title">
        <v-icon color="black" size="small" start> mdi-tray-full </v-icon>
        Jobs
      </h4>
      <v-btn
        color="secondary"
        class="black--text"
        size="small"
        variant="flat"
        @click.stop="openModal = true"
      >
        Add
      </v-btn>
    </header>
    <v-table v-if="jobs.length > 0">
      <template v-slot:default>
        <thead>
          <tr>
            <th class="text-left">Job ID</th>
            <th class="text-left">Type</th>
            <th class="text-left">Date</th>
            <th class="text-center">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="job in jobs" :key="job.jobId">
            <td>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <v-chip
                    class="text-center clip"
                    v-bind="props"
                    variant="outlined"
                    tile
                  >
                    {{ job.jobId }}
                  </v-chip>
                </template>
                <span>{{ job.jobId }}</span>
              </v-tooltip>
            </td>
            <td class="capitalize">{{ job.jobType.replace("_", " ") }}</td>
            <td>{{ formatDate(job.enqueuedAt) }}</td>
            <td class="text-center">
              <v-chip
                class="ma-2"
                :color="getColor(job.status)"
                text-color="white"
              >
                {{ job.status }}
              </v-chip>
            </td>
          </tr>
        </tbody>
      </template>
    </v-table>
    <div v-if="jobs.length > 0" class="text-center pa-4">
      <v-pagination
        v-model="page"
        :length="pageCount"
        :total-visible="5"
        @update:modelValue="getPaginatedJobs($event)"
      ></v-pagination>
    </div>
    <p v-else class="text-subtitle-1 pa-7">There are no jobs in the queue.</p>
    <job-modal v-model:is-open="openModal" v-bind="$attrs" />
  </v-container>
</template>

<script>
import JobModal from "./JobModal.vue";

export default {
  name: "JobsTable",
  components: { JobModal },
  props: {
    getJobs: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      jobs: [],
      page: 1,
      pageSize: 10,
      pageCount: 1,
      openModal: false,
    };
  },
  created() {
    this.getPaginatedJobs(1);
  },
  methods: {
    async getPaginatedJobs(page = this.page, pageSize = this.pageSize) {
      let response = await this.getJobs(page, pageSize);
      if (response) {
        this.jobs = response.data.jobs.entities;
        this.pageCount = response.data.jobs.pageInfo.numPages;
        this.page = response.data.jobs.pageInfo.page;
      }
    },
    getColor(status) {
      if (status === "finished") {
        return "#3fa500";
      } else if (status === "failed") {
        return "#f41900";
      } else if (status === "started") {
        return "primary";
      } else {
        return "rgba(0, 0, 0, 0.42)";
      }
    },
    formatDate(dateTime) {
      return dateTime ? new Date(dateTime).toLocaleString("en-US") : "-";
    },
  },
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.capitalize {
  text-transform: capitalize;
}
.container {
  max-width: 1160px;
}
.clip :deep(.v-chip__content) {
  max-width: 8ch;
  overflow: hidden;
  text-overflow: clip;
  font-family: monospace;
}
</style>
