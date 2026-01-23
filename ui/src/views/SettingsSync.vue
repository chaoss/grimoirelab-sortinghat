<template>
  <tasks-table
    :fetch-backends="fetchBackends"
    :fetch-tasks="fetchTasks"
    :create-task="createTask"
    :delete-task="deleteTask"
    :edit-task="editTask"
  />
</template>
<script>
import { getImporterTypes, getImportIdentitiesTasks } from "../apollo/queries";
import {
  scheduleTask,
  deleteImportTask,
  updateImportTask,
} from "../apollo/mutations";
import TasksTable from "../components/TasksTable";

export default {
  name: "SettingsSync",
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
    async createTask(job, interval, params) {
      const response = await scheduleTask(this.$apollo, job, interval, params);
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
