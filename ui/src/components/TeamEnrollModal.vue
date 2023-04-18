<template>
  <v-dialog v-model="isOpen" persistent max-width="650">
    <v-card class="section">
      <v-card-title class="header">
        <span v-if="team" class="title">
          Add to {{ team }} in {{ organization }}
        </span>
        <span v-else class="title">Add to {{ organization }} team</span>
      </v-card-title>
      <v-card-text class="mt-3">
        <v-form ref="form">
          <v-row>
            <v-col v-if="!team" cols="4">
              <v-text-field
                v-model="form.team"
                :rules="validations.required"
                label="Team"
                outlined
                dense
              />
            </v-col>
            <v-col :cols="team ? 6 : 4">
              <date-input
                v-model="form.dateFrom"
                :max="form.dateTo"
                label="Date from"
                outlined
              />
            </v-col>
            <v-col :cols="team ? 6 : 4">
              <date-input
                v-model="form.dateTo"
                :min="form.dateFrom"
                label="Date to"
                outlined
              />
            </v-col>
          </v-row>
        </v-form>

        <v-alert v-if="errorMessage" text type="error">
          {{ errorMessage }}
        </v-alert>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary darken-1" text @click.prevent="closeModal">
            Cancel
          </v-btn>
          <v-btn
            depressed
            color="primary"
            :disabled="!team && !form.team"
            @click.prevent="onSave"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import DateInput from "./DateInput.vue";

export default {
  name: "TeamEnrollModal",
  components: { DateInput },
  props: {
    isOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
    uuid: {
      type: String,
      required: true,
    },
    enrollments: {
      type: Array,
      required: false,
    },
    organization: {
      type: String,
      required: false,
    },
    team: {
      type: String,
      required: false,
    },
    enroll: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      form: {
        team: null,
        dateFrom: null,
        dateTo: null,
      },
      validations: {
        required: [(value) => !!value || "Required"],
      },
      errorMessage: null,
    };
  },
  methods: {
    closeModal() {
      this.$emit("update:isOpen", false);
      this.$emit("updateTable");
      this.$refs.form.reset();
      this.form = [
        {
          team: null,
          dateFrom: null,
          dateTo: null,
        },
      ];
      this.errorMessage = null;
    },
    async onSave() {
      const isValid = this.$refs.form.validate();
      if (!isValid) {
        return;
      }

      try {
        const group = this.team || this.form.team;
        if (
          !this.enrollments.some(
            (enrollment) => enrollment.group.name === this.organization
          )
        ) {
          this.enroll(
            this.uuid,
            this.organization,
            this.form.dateFrom,
            this.form.dateTo
          );
        }
        const response = await this.enroll(
          this.uuid,
          group,
          this.form.dateFrom,
          this.form.dateTo,
          this.organization
        );

        if (response && !response.errors) {
          this.$logger.debug(`Enrolled individual ${this.uuid}`, {
            uuid: this.uuid,
            group: group,
            parentOrg: this.organization,
            fromDate: this.form.dateFrom,
            toDate: this.form.dateTo,
          });
          this.$emit("updateIndividual", response.data.enroll.individual);
          this.closeModal();
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(
          `Error enrolling individual ${this.uuid}: ${error}`,
          this.form
        );
      }
    },
  },
};
</script>
