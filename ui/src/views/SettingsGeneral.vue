<template>
  <section class="section">
    <header class="header">
      <h1 class="title">General settings</h1>
    </header>
    <v-progress-linear v-if="isLoading" color="primary" indeterminate />
    <v-expansion-panels v-else accordion flat>
      <v-expansion-panel>
        <v-expansion-panel-header aria-label="Show advanced configuration">
          <v-row class="ma-0 px-2">
            <v-col>
              <p class="subheader mb-0">
                Affiliate to organizations automatically
              </p>
              <span
                v-if="tasks.affiliate.lastExecution"
                class="v-list-item__subtitle text--secondary mt-3"
              >
                <v-icon v-if="tasks.affiliate.failed" color="error" left small>
                  mdi-alert
                </v-icon>
                <v-icon v-else color="green" left small> mdi-check </v-icon>
                Last run {{ formatDate(tasks.affiliate.lastExecution) }}
              </span>
            </v-col>
            <v-col class="d-flex justify-end">
              <v-switch
                v-model="tasks.affiliate.isActive"
                class="mt-0"
                dense
                inset
                hide-details
                @change="toggleTask('affiliate')"
                @click.stop
                @mousedown.prevent
              >
                <template v-slot:label>
                  <label class="d-sr-only"> Affiliate to organizations </label>
                </template>
              </v-switch>
            </v-col>
          </v-row>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row class="ma-0 pt-4 pl-2">
            <v-col class="pa-0">
              <p class="text-subtitle-2">Advanced configuration</p>
            </v-col>
          </v-row>
          <v-form>
            <v-row class="ma-0 pl-2">
              <v-col cols="3" class="pa-0">
                <v-radio-group
                  v-model="tasks.affiliate.interval"
                  class="mt-0"
                  dense
                >
                  <template v-slot:label>
                    <h3 class="subheader text--secondary">Interval</h3>
                  </template>
                  <v-radio :value="1440" label="Every day"></v-radio>
                  <v-radio :value="10080" label="Every week"></v-radio>
                  <v-radio :value="43800" label="Every month"></v-radio>
                  <v-radio value="custom" label="Custom"></v-radio>
                </v-radio-group>
                <v-text-field
                  v-model="tasks.affiliate.customInterval"
                  label="Every"
                  type="number"
                  suffix="minutes"
                  class="ml-8"
                  dense
                  hide-details
                  outlined
                >
                </v-text-field>
              </v-col>
            </v-row>
            <v-row v-if="tasks.affiliate.isActive" class="ma-0 pt-8 pl-2">
              <v-col class="pa-0">
                <v-btn
                  color="primary"
                  depressed
                  small
                  @click="updateScheduledTask('affiliate')"
                >
                  Update
                </v-btn>
              </v-col>
            </v-row>
          </v-form>
        </v-expansion-panel-content>
      </v-expansion-panel>
      <v-expansion-panel>
        <v-expansion-panel-header aria-label="Show advanced configuration">
          <v-row class="ma-0 px-2">
            <v-col>
              <p class="subheader mb-0">Unify profiles automatically</p>
              <span v-if="tasks.unify.lastExecution" class="mt-3">
                <v-icon v-if="tasks.unify.failed" color="error" left small>
                  mdi-alert
                </v-icon>
                <v-icon v-else color="green" left small> mdi-check </v-icon>
                <span class="v-list-item__subtitle text--secondary">
                  Last run {{ formatDate(tasks.unify.lastExecution) }}
                </span>
              </span>
            </v-col>
            <v-col class="d-flex justify-end">
              <v-switch
                v-model="tasks.unify.isActive"
                dense
                inset
                hide-details
                class="mt-0"
                @change="toggleTask('unify')"
                @click.stop
                @mousedown.prevent
              >
                <template v-slot:label>
                  <label class="d-sr-only">Unify profiles automatically</label>
                </template>
              </v-switch>
            </v-col>
          </v-row>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <v-row class="ma-0 pt-4 pl-2">
            <v-col class="pa-0">
              <p class="text-subtitle-2">Advanced configuration</p>
            </v-col>
          </v-row>
          <v-form>
            <v-row class="ma-0 pl-2">
              <v-col class="pa-0 mb-3">
                <v-checkbox
                  v-model="tasks.unify.params.exclude"
                  label="Exclude individuals in RecommenderExclusionTerm list"
                  dense
                  hide-details
                />
                <v-checkbox
                  v-model="tasks.unify.params.strict"
                  label="Exclude individuals with invalid email addresses and names"
                  dense
                  hide-details
                />
                <v-checkbox
                  v-model="tasks.unify.params.match_source"
                  label="Only unify identities that share the same source"
                  dense
                  hide-details
                />
              </v-col>
            </v-row>
            <v-row class="ma-0 pl-2">
              <v-col cols="3" class="pa-0 mb-2">
                <h3 class="subheader text--secondary">
                  Unify profiles based on their
                </h3>
                <v-checkbox
                  v-model="tasks.unify.params.criteria"
                  label="Name"
                  value="name"
                  dense
                  hide-details
                />
                <v-checkbox
                  v-model="tasks.unify.params.criteria"
                  label="Email"
                  value="email"
                  dense
                  hide-details
                />
                <v-checkbox
                  v-model="tasks.unify.params.criteria"
                  label="Username"
                  value="username"
                  dense
                  hide-details
                />
              </v-col>
            </v-row>
            <v-row class="ma-0 pl-2">
              <v-col cols="3" class="pa-0">
                <v-radio-group
                  v-model="tasks.unify.interval"
                  class="mt-0"
                  dense
                >
                  <template v-slot:label>
                    <h3 class="subheader text--secondary">Interval</h3>
                  </template>
                  <v-radio :value="1440" label="Every day"></v-radio>
                  <v-radio :value="10080" label="Every week"></v-radio>
                  <v-radio :value="43800" label="Every month"></v-radio>
                  <v-radio value="custom" label="Custom"></v-radio>
                </v-radio-group>
                <v-text-field
                  v-model="tasks.unify.customInterval"
                  label="Every"
                  type="number"
                  suffix="minutes"
                  class="ml-8"
                  dense
                  hide-details
                  outlined
                >
                </v-text-field>
              </v-col>
            </v-row>
            <v-row v-if="tasks.unify.isActive" class="ma-0 pt-8 pl-2">
              <v-col class="pa-0">
                <v-btn
                  color="primary"
                  depressed
                  small
                  @click="updateScheduledTask('unify')"
                >
                  Update
                </v-btn>
              </v-col>
            </v-row>
          </v-form>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
    <v-snackbar
      v-model="snackbar.isActive"
      :color="snackbar.color"
      timeout="4000"
      text
    >
      {{ snackbar.text }}
    </v-snackbar>
  </section>
</template>
<script>
import { getScheduledTasks } from "../apollo/queries";
import { scheduleTask, deleteTask, updateTask } from "../apollo/mutations";

export default {
  name: "SettingsGeneral",
  data() {
    return {
      isLoading: true,
      tasks: {
        affiliate: {
          isActive: false,
          interval: 10080,
          customInterval: "",
          failed: false,
          lastExecution: null,
          id: null,
          params: {},
        },
        unify: {
          isActive: false,
          interval: 10080,
          failed: false,
          lastExecution: null,
          id: null,
          params: {
            criteria: ["name", "email", "username"],
            exclude: true,
            strict: true,
            match_source: false,
          },
        },
      },
      snackbar: {
        isActive: false,
        text: "",
        color: "success",
      },
    };
  },
  methods: {
    async fetchScheduledTasks() {
      this.isLoading = true;

      const query = await getScheduledTasks(this.$apollo);
      const tasks = query.data.scheduledTasks.entities;
      const affiliateTask = tasks.find((task) => task.jobType === "affiliate");
      const unifyTask = tasks.find((task) => task.jobType === "unify");

      if (affiliateTask) {
        this.buildForm(affiliateTask);
      }
      if (unifyTask) {
        this.buildForm(unifyTask);
      }
      this.isLoading = false;
    },
    buildForm(task) {
      const intervals = [1440, 10080, 43800];
      const interval = intervals.find((interval) => interval === task.interval)
        ? task.interval
        : "custom";

      Object.assign(this.tasks[task.jobType], {
        isActive: true,
        interval: interval,
        failed: task.failed,
        lastExecution: task.lastExecution,
        id: task.id,
        customInterval: task.interval,
        params: task.args,
      });
    },
    formatDate(dateTime) {
      return new Date(dateTime).toLocaleString();
    },
    toggleTask(job) {
      if (this.tasks[job].isActive) {
        this.createTask(job);
      } else {
        this.deleteScheduledTask(job);
      }
    },
    async createTask(job) {
      const interval =
        this.tasks[job].interval === "custom"
          ? this.tasks[job].customInterval
          : this.tasks[job].interval;
      const task = await scheduleTask(
        this.$apollo,
        job,
        interval,
        JSON.stringify(this.tasks[job].params)
      ).catch((error) => {
        this.openSnackbar(error);
        this.tasks[job].isActive = false;
      });

      Object.assign(this.tasks[job], {
        isActive: true,
        id: task.data.scheduleTask.task.id,
        lastExecution: task.data.scheduleTask.task.lastExecution,
        failed: task.data.scheduleTask.task.failed,
      });
      this.openSnackbar();
    },
    async deleteScheduledTask(job) {
      const response = await deleteTask(this.$apollo, this.tasks[job].id).catch(
        (error) => this.openSnackbar(error)
      );

      if (response.data.deleteScheduledTask.deleted) {
        Object.assign(this.tasks[job], {
          isActive: false,
          id: null,
          lastExecution: null,
          failed: null,
        });
        this.openSnackbar();
      }
    },
    async updateScheduledTask(job) {
      const interval =
        this.tasks[job].interval === "custom"
          ? this.tasks[job].customInterval
          : this.tasks[job].interval;
      const data = {
        interval: interval,
        params: JSON.stringify(this.tasks[job].params),
      };

      await updateTask(this.$apollo, this.tasks[job].id, data).catch((error) =>
        this.openSnackbar(error)
      );
      this.openSnackbar();
    },
    openSnackbar(error) {
      const text = error
        ? `Error saving settings: ${this.$getErrorMessage(error)}`
        : `Changes saved successfully`;

      Object.assign(this.snackbar, {
        isActive: true,
        text: text,
        color: error ? "error" : "success",
      });
    },
  },
  async mounted() {
    await this.fetchScheduledTasks();
  },
};
</script>
<style lang="scss" scoped>
.v-expansion-panel::after {
  border-top: thin solid;
}

.v-expansion-panel--active > .v-expansion-panel-header {
  min-height: unset;
}

.v-expansion-panel-header {
  align-items: flex-start;

  &:hover {
    background-color: #f6f6f6;
  }

  .col {
    padding: 0;
  }
}

::v-deep .v-expansion-panel-header__icon {
  margin-top: 4px;
}

.v-expansion-panel-content {
  border-top: thin solid rgba(0, 0, 0, 0.08);
}

::v-deep .v-label,
::v-deep .v-text-field__suffix {
  font-size: 0.875rem;
}

.subheader {
  line-height: 1.775rem;
}
</style>
