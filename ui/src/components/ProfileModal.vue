<template>
  <v-dialog v-model="isOpen" persistent max-width="650">
    <v-card class="section">
      <v-card-title class="header">
        <span class="title">Add individual</span>
      </v-card-title>
      <v-card-text class="mt-3">
        <v-form ref="form">
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Name"
                id="name"
                v-model="profileForm.name"
                outlined
                dense
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Email"
                id="email"
                v-model="profileForm.email"
                :rules="validations.email"
                outlined
                dense
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Username"
                id="username"
                v-model="profileForm.username"
                outlined
                dense
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Source"
                id="source"
                v-model="profileForm.source"
                :rules="validations.required"
                outlined
                dense
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Gender"
                v-model="profileForm.gender"
                outlined
                dense
              />
            </v-col>
            <v-col cols="4">
              <v-combobox
                v-model="profileForm.country"
                :items="countries"
                label="Country"
                item-text="name"
                outlined
                dense
                @click.once="getCountryList"
              />
            </v-col>
            <v-col cols="2">
              <v-checkbox
                v-model="profileForm.isBot"
                label="Bot"
                color="primary"
                class="mt-1"
              >
              </v-checkbox>
            </v-col>
          </v-row>

          <v-row class="pl-4">
            <span class="subheader">Organizations</span>
          </v-row>
          <v-row v-for="(enrollment, index) in enrollmentsForm" :key="index">
            <v-col cols="4">
              <organization-selector
                v-model="enrollmentsForm[index].organization"
                :fetch-organizations="fetchOrganizations"
              />
            </v-col>
            <v-col cols="3">
              <date-input
                v-model="enrollmentsForm[index].fromDate"
                :max="enrollmentsForm[index].toDate"
                label="Date from"
                outlined
              />
            </v-col>
            <v-col cols="3">
              <date-input
                v-model="enrollmentsForm[index].toDate"
                :min="enrollmentsForm[index].fromDate"
                label="Date to"
                outlined
              />
            </v-col>
            <v-col cols="1" class="pt-3">
              <v-btn icon color="primary" @click="removeEnrollment(index)">
                <v-icon color="primary">mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row class="pl-3">
            <v-btn text small outlined color="primary" @click="addInput">
              <v-icon left small color="primary"
                >mdi-plus-circle-outline</v-icon
              >
              Add organization
            </v-btn>
          </v-row>
        </v-form>
      </v-card-text>

      <v-alert v-if="errorMessage" text type="error" class="ma-5">
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
          :disabled="disableSave"
          @click.prevent="onSave"
        >
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import DateInput from "./DateInput.vue";
import OrganizationSelector from "./OrganizationSelector";

export default {
  name: "ProfileModal",
  components: { DateInput, OrganizationSelector },
  props: {
    isOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
    addIdentity: {
      type: Function,
      required: true,
    },
    updateProfile: {
      type: Function,
      required: true,
    },
    enroll: {
      type: Function,
      required: true,
    },
    getCountries: {
      type: Function,
      required: true,
    },
    fetchOrganizations: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      profileForm: {
        name: "",
        email: "",
        username: "",
        source: "",
        nationality: "",
        gender: "",
        isBot: false,
        countries: [],
      },
      enrollmentsForm: [
        {
          organization: "",
          fromDate: "",
          toDate: "",
        },
      ],
      savedData: {
        individual: undefined,
        profile: undefined,
        enrollments: undefined,
      },
      validations: {
        required: [(value) => !!value || "Required"],
        email: [
          (value) =>
            (value ? /\S+@\S+\.\S+/.test(value) : true) || "Invalid email",
        ],
      },
      errorMessage: "",
      countries: [],
    };
  },
  computed: {
    disableSave() {
      return [
        this.profileForm.name,
        this.profileForm.email,
        this.profileForm.username,
      ].every((value) => value === "");
    },
  },
  methods: {
    addInput() {
      this.enrollmentsForm.push({
        organization: "",
        fromDate: "",
        toDate: "",
      });
    },
    removeEnrollment(index) {
      this.enrollmentsForm.splice(index, 1);
    },
    closeModal() {
      this.$emit("update:isOpen", false);
      this.$emit("updateTable");
      this.$refs.form.reset();
      this.enrollmentsForm = [
        {
          organization: "",
          fromDate: "",
          toDate: "",
        },
      ];
      this.savedData = {
        individual: undefined,
        profile: undefined,
        enrollments: undefined,
      };
      this.errorMessage = "";
    },
    async onSave() {
      const isValid = this.$refs.form.validate();
      if (!isValid) {
        return;
      }
      if (!this.savedData.individual) {
        const uuid = await this.createIndividual();
        if (uuid) {
          const profile = await this.addProfileInfo(uuid);
          const enrollments = await this.addEnrollments(uuid);
          if (profile && enrollments) {
            this.closeModal();
          }
        }
      } else {
        const profile = await this.addProfileInfo(this.savedData.individual);
        if (profile) {
          const enrollments = await this.addEnrollments(
            this.savedData.individual
          );
          if (enrollments) {
            this.closeModal();
          }
        }
      }
    },
    async createIndividual() {
      const data = {
        email: this.profileForm.email === "" ? null : this.profileForm.email,
        name: this.profileForm.name === "" ? null : this.profileForm.name,
        source: this.profileForm.source,
        username:
          this.profileForm.username === "" ? null : this.profileForm.username,
      };
      try {
        const response = await this.addIdentity(
          data.email,
          data.name,
          data.source,
          data.username
        );
        if (response && response.data.addIdentity) {
          this.savedData.individual = response.data.addIdentity.uuid;
          this.$logger.debug("Added identity", data);
          return this.savedData.individual;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error adding identity: ${error}`, data);
      }
    },
    async addProfileInfo(uuid) {
      const data = {
        gender: this.profileForm.gender,
        countryCode: this.profileForm.country
          ? this.profileForm.country.code
          : null,
        isBot: this.profileForm.isBot,
      };
      try {
        const response = await this.updateProfile(data, uuid);
        if (response && response.data.updateProfile) {
          this.savedData.profile = response.data.updateProfile;
          this.$logger.debug(`Updated individual ${uuid} profile`, data);
          return this.savedData.profile;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error updating profile ${uuid}: ${error}`, data);
      }
    },
    async addEnrollments() {
      try {
        const response = await Promise.all(
          this.enrollmentsForm.map((enrollment) => {
            if (enrollment.organization) {
              const response = this.enroll(
                this.savedData.individual,
                enrollment.organization,
                enrollment.fromDate,
                enrollment.toDate
              );
              this.$logger.debug(
                `Enrolled individual ${this.savedData.individual}`,
                {
                  uuid: this.savedData.individual,
                  organization: enrollment.organization,
                  fromDate: enrollment.fromDate,
                  toDate: enrollment.toDate,
                }
              );
              return response;
            }
          })
        );
        if (response) {
          this.$emit("updateOrganizations");
          return response;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(
          `Error enrolling individual ${this.savedData.individual}: ${error}`,
          this.enrollmentsForm
        );
      }
    },
    async getCountryList() {
      const response = await this.getCountries();
      if (response) {
        this.countries = response;
      }
    },
  },
};
</script>
