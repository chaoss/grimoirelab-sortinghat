<template>
  <v-dialog v-model="isOpen" max-width="500px" @click:outside="closeModal">
    <v-card class="pa-3">
      <v-card-title class="headline">Recommend matches</v-card-title>
      <v-card-text v-if="jobId">
        <v-alert type="success" text>
          <p>
            Enqueued job <code>{{ jobId }}</code> to recommend matches.
          </p>
          <router-link :to="{ name: 'Jobs' }" target="_blank">
            View jobs
          </router-link>
        </v-alert>
      </v-card-text>
      <v-card-text v-else>
        <p class="subtitle-2 mt-2">
          Find possible matches based on this profile's:
        </p>
        <div>
          <v-checkbox
            v-model="form.criteria"
            label="Name"
            value="name"
            dense
            hide-details
          ></v-checkbox>
          <v-checkbox
            v-model="form.criteria"
            label="Email"
            value="email"
            dense
            hide-details
          ></v-checkbox>
          <v-checkbox
            v-model="form.criteria"
            label="Username"
            value="username"
            dense
          ></v-checkbox>
        </div>
        <v-divider></v-divider>
        <div class="my-4">
          <v-checkbox
            v-model="form.strict"
            label="Strict matching criteria"
            dense
            hide-details
          />
          <v-checkbox
            v-model="form.exclude"
            label="Exclude individuals in RecommenderExclusionTerm list"
            dense
            hide-details
          ></v-checkbox>
        </div>
        <v-alert v-if="error" dense text type="error">
          {{ error }}
        </v-alert>
      </v-card-text>
      <v-card-actions v-if="jobId">
        <v-spacer></v-spacer>
        <v-btn text color="primary" @click="closeModal"> OK </v-btn>
      </v-card-actions>
      <v-card-actions v-else>
        <v-spacer></v-spacer>
        <v-btn text @click="closeModal"> Cancel </v-btn>
        <v-btn color="primary" id="confirm" depressed @click.stop="createJob">
          Confirm
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: "MatchesModal",
  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
    recommendMatches: {
      type: Function,
      required: true,
    },
    uuid: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      form: {
        criteria: ["name", "email", "username"],
        exclude: true,
        strict: true,
      },
      jobId: null,
      error: null,
    };
  },
  methods: {
    closeModal() {
      this.$emit("update:isOpen", false);
      this.form = {
        criteria: ["name", "email", "username"],
        exclude: true,
        strict: true,
      };
      this.error = null;
      this.jobId = null;
    },
    async createJob() {
      try {
        const response = await this.recommendMatches(
          this.form.criteria,
          this.form.exclude,
          this.form.strict,
          [this.uuid]
        );
        this.jobId = response.data.recommendMatches.jobId;
      } catch (error) {
        this.error = this.$getErrorMessage(error);
        this.$logger.error(`Error recommending matches: ${error}`);
      }
    },
  },
};
</script>
