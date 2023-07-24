<template>
  <v-container class="section jobs mt-6 pa-0">
    <header class="header">
      <h1 class="title">Import identities</h1>
      <v-menu offset-y>
        <template v-slot:activator="{ on }">
          <v-btn color="primary" depressed small v-on="on">
            Select source
            <v-icon color="white" small right>mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list v-if="importers" dense>
          <v-list-item
            v-for="(backend, index) in importers"
            :key="index"
            @click="openModal(backend)"
          >
            <v-list-item-title>
              {{ backend.name }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </header>
    <v-alert v-if="error" text type="error">
      {{ error }}
    </v-alert>
    <v-progress-linear
      v-if="isLoading"
      indeterminate
      color="primary"
    ></v-progress-linear>
    <v-simple-table>
      <template v-slot:default>
        <thead v-if="tasks.length > 0">
          <tr>
            <th class="text-left">Source</th>
            <th class="text-left">Last run</th>
            <th class="text-left">Next run</th>
            <th class="text-right">Executions</th>
            <th class="text-right">Failures</th>
            <th></th>
          </tr>
        </thead>
        <div v-else class="ma-9">
          <h3 class="text-h6">No scheduled tasks</h3>
          <p class="text-body-2">
            You can sync identities from different data sources automatically
            and periodically.
          </p>
        </div>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>
              <span class="font-weight-medium">
                {{ task.args.backend_name }}
              </span>
            </td>
            <td>
              <v-icon
                v-if="task.lastExecution"
                :color="task.failed ? 'failed' : 'finished'"
                :aria-label="task.failed ? 'failed' : 'finished'"
                aria-hidden="false"
                class="mb-1 mr-1"
                small
              >
                {{ task.failed ? "mdi-alert-circle" : "mdi-check-circle" }}
              </v-icon>
              {{ formatDate(task.lastExecution) }}
            </td>
            <td>{{ formatDate(task.scheduledDatetime) }}</td>
            <td class="text-right">{{ task.executions }}</td>
            <td class="text-right">{{ task.failures }}</td>
            <td class="text-right pr-8">
              <v-btn
                class="mr-2"
                color="primary"
                text
                small
                outlined
                @click="openModal(task.args.backend_name, task)"
              >
                <v-icon small>mdi-pencil</v-icon>
                <span class="d-sr-only">Edit task</span>
              </v-btn>
              <v-btn
                color="primary"
                text
                small
                outlined
                @click="deleteItem(task.id)"
              >
                <v-icon small>mdi-delete</v-icon>
                <span class="d-sr-only">Delete task</span>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </template>
    </v-simple-table>
    <importer-modal
      v-if="modal.isOpen"
      :is-open="modal.isOpen"
      :create-task="createTask"
      :edit-task="editTask"
      :task="modal.task"
      :importer="modal.importer"
      @update:open="modal.isOpen = $event"
      @update:tasks="getTasks()"
    />
  </v-container>
</template>
<script>
import ImporterModal from "./ImporterModal";
export default {
  name: "TasksTable",
  components: { ImporterModal },
  props: {
    fetchBackends: {
      type: Function,
      required: true,
    },
    fetchTasks: {
      type: Function,
      required: true,
    },
    createTask: {
      type: Function,
      required: true,
    },
    deleteTask: {
      type: Function,
      required: true,
    },
    editTask: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      importers: [],
      tasks: [],
      error: null,
      isLoading: false,
      modal: {
        isOpen: false,
        task: {},
        importer: {},
      },
    };
  },
  methods: {
    formatDate(dateTime) {
      if (!dateTime) {
        return "-";
      }
      return new Date(dateTime).toLocaleString();
    },
    openModal(backend, task = {}) {
      if (typeof backend === "string") {
        backend = this.importers.find((importer) => importer.name === backend);
      }
      Object.assign(this.modal, {
        isOpen: true,
        importer: backend,
        task,
      });
    },
    async getBackends() {
      try {
        const response = await this.fetchBackends();
        this.importers = response.data.identitiesImportersTypes;
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      }
    },
    async getTasks() {
      try {
        this.isLoading = true;
        const response = await this.fetchTasks();
        this.tasks = response.data.scheduledTasks.entities;
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      } finally {
        this.isLoading = false;
      }
    },
    async deleteItem(id) {
      try {
        const response = await this.deleteTask(id);
        if (response.data.deleteScheduledTask) {
          this.getTasks();
        }
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      }
    },
  },
  async mounted() {
    this.getTasks();
    await this.getBackends();
  },
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
</style>
