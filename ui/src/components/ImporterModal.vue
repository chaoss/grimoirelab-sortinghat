<template>
  <v-dialog
    v-model="isOpen"
    max-width="450"
    @click:outside="$emit('update:open')"
  >
    <v-card class="section">
      <v-card-title class="header title">
        Import identities from {{ importer.name }}
      </v-card-title>
      <v-card-text class="mt-3">
        <h3 class="subheader mb-2">Settings</h3>
        <v-row class="pa-3">
          <v-text-field
            v-model="form.url"
            label="URL"
            dense
            hide-details
            outlined
          />
        </v-row>
        <v-row v-for="(value, field) in form.fields" :key="field" class="pa-3">
          <v-text-field
            v-model="form.fields[field]"
            :label="field"
            dense
            hide-details
            outlined
          />
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-radio-group v-model="form.interval" class="mt-0" dense>
              <template v-slot:label>
                <h3 class="subheader">Run script</h3>
              </template>
              <v-radio :value="0" label="Once"></v-radio>
              <v-radio :value="10080" label="Every week"></v-radio>
              <v-radio :value="43800" label="Every month"></v-radio>
              <v-radio value="custom" label="Custom"></v-radio>
            </v-radio-group>
            <v-text-field
              v-model="form.customInterval"
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

        <v-alert v-if="error" text type="error" class="ma-5">
          {{ error }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" text @click="onClose"> Cancel </v-btn>

        <v-btn color="primary" depressed :disabled="!form.url" @click="onSave">
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: "ImporterModal",
  props: {
    importer: {
      type: Object,
      required: true,
    },
    task: {
      type: Object,
      required: true,
    },
    createTask: {
      type: Function,
      required: true,
    },
    editTask: {
      type: Function,
      required: true,
    },
    isOpen: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      form: {
        fields: {},
        interval: this.task.interval || 0,
        customInterval: "",
        url: "",
      },
      error: null,
    };
  },
  methods: {
    onSave() {
      if (this.task.id) {
        this.updateTask();
      } else {
        this.addTask();
      }
    },
    onClose() {
      this.$emit("update:open", false);
    },
    async addTask() {
      try {
        const interval =
          this.form.interval === "custom"
            ? this.form.customInterval
            : this.form.interval;
        const params = JSON.stringify(this.form.fields);
        const response = await this.createTask(
          this.importer.name,
          interval,
          params,
          this.form.url
        );
        if (response && !response.errors) {
          this.$emit("update:open", false);
          this.$emit("update:tasks");
        }
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      }
    },
    async updateTask() {
      try {
        const interval =
          this.form.interval === "custom"
            ? this.form.customInterval
            : this.form.interval;
        const data = {
          url: this.form.url,
          interval: interval,
          params: JSON.stringify(this.form.fields),
        };
        const response = await this.editTask(this.task.id, data);
        if (response && !response.errors) {
          this.$emit("update:open", false);
          this.$emit("update:tasks");
        }
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      }
    },
    buildForm() {
      const intervals = [0, 10080, 43800];
      const taskArgs = this.task.args || {};
      const fields = this.importer.args.reduce(
        (accumulator, arg) => ({ ...accumulator, [arg]: taskArgs[arg] }),
        {}
      );
      const { url, ...rest } = fields;
      this.form.url = url || this.task.url;
      this.form.fields = rest;
      if (
        this.task.interval &&
        !intervals.find((interval) => interval === this.task.interval)
      ) {
        this.form.customInterval = this.task.interval;
        this.form.interval = "custom";
      }
    },
  },
  mounted() {
    this.buildForm();
  },
};
</script>
