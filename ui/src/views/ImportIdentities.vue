<template>
  <v-main>
    <tasks-table
      :fetch-backends="fetchBackends"
      :fetch-tasks="fetchTasks"
      :create-task="createTask"
      :delete-task="deleteTask"
      :edit-task="editTask"
    />
  </v-main>
</template>
<script>
import {
  getImporterTypes,
  getImportIdentitiesTasks,
} from "./../apollo/queries";
import {
  importIdentities,
  deleteImportTask,
  updateImportTask,
} from "./../apollo/mutations";
import TasksTable from "./../components/TasksTable";

export default {
  name: "ImportIdentities",
  components: { TasksTable },
  methods: {
    async fetchBackends() {
      const response = await getImporterTypes(this.$apollo);
      return response;
    },
    async fetchTasks() {
      const response = await getImportIdentitiesTasks(this.$apollo);
      return response;
    },
    async createTask(backend, interval, params, url) {
      const response = await importIdentities(
        this.$apollo,
        backend,
        interval,
        params,
        url
      );
      return response;
    },
    async deleteTask(id) {
      const response = await deleteImportTask(this.$apollo, id);
      return response;
    },
    async editTask(id, data) {
      const response = await updateImportTask(this.$apollo, id, data);
      return response;
    },
  },
};
</script>
<style lang="scss" scoped>
.container {
  max-width: 1160px;
}
</style>
