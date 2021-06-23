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
                v-model="profileForm.name"
                outlined
                dense
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Email"
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
                v-model="profileForm.username"
                outlined
                dense
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Source"
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
        </v-form>

        <v-row class="pl-4">
          <span class="subheader">Organizations</span>
        </v-row>
        <v-row v-for="(enrollment, index) in enrollmentsForm" :key="index">
          <v-col cols="4">
            <v-text-field
              label="Organization"
              v-model="enrollmentsForm[index].organization"
              outlined
              dense
            />
          </v-col>
          <v-col cols="3">
            <v-menu
              v-model="enrollmentsForm[index].fromDateMenu"
              :close-on-content-click="false"
              transition="scale-transition"
              offset-y
              min-width="290px"
            >
              <template v-slot:activator="{ on }">
                <v-text-field
                  v-model="enrollmentsForm[index].fromDate"
                  label="Date from"
                  outlined
                  dense
                  readonly
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="enrollmentsForm[index].fromDate"
                @input="enrollmentsForm[index].fromDateMenu = false"
                no-title
                scrollable
              >
              </v-date-picker>
            </v-menu>
          </v-col>
          <v-col cols="3">
            <v-menu
              v-model="enrollmentsForm[index].toDateMenu"
              :close-on-content-click="false"
              transition="scale-transition"
              offset-y
              min-width="290px"
            >
              <template v-slot:activator="{ on }">
                <v-text-field
                  v-model="enrollmentsForm[index].toDate"
                  label="Date to"
                  outlined
                  dense
                  readonly
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="enrollmentsForm[index].toDate"
                :min="enrollmentsForm[index].fromDate"
                @input="enrollmentsForm[index].toDateMenu = false"
                no-title
                scrollable
              >
              </v-date-picker>
            </v-menu>
          </v-col>
          <v-col cols="1" class="pt-3">
            <v-btn icon color="primary" @click="removeEnrollment(index)">
              <v-icon color="primary">mdi-delete</v-icon>
            </v-btn>
          </v-col>
        </v-row>
        <v-row class="pl-3">
          <v-btn text small outlined color="primary" @click="addInput">
            <v-icon left small color="primary">mdi-plus-circle-outline</v-icon>
            Add organization
          </v-btn>
        </v-row>
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
export default {
  name: "ProfileModal",
  props: {
    isOpen: {
      type: Boolean,
      required: false,
      default: false
    },
    addIdentity: {
      type: Function,
      required: true
    },
    updateProfile: {
      type: Function,
      required: true
    },
    enroll: {
      type: Function,
      required: true
    },
    getCountries: {
      type: Function,
      required: true
    }
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
        countries: []
      },
      enrollmentsForm: [
        {
          organization: "",
          fromDate: "",
          fromDateMenu: false,
          toDate: "",
          toDateMenu: false
        }
      ],
      savedData: {
        individual: undefined,
        profile: undefined,
        enrollments: undefined
      },
      validations: {
        required: [value => !!value || "Required"],
        email: [
          value =>
            (value ? /\S+@\S+\.\S+/.test(value) : true) || "Invalid email"
        ]
      },
      errorMessage: "",
      countries: []
    };
  },
  computed: {
    disableSave() {
      return [
        this.profileForm.name,
        this.profileForm.email,
        this.profileForm.username
      ].every(value => value === "");
    }
  },
  methods: {
    addInput() {
      this.enrollmentsForm.push({
        organization: "",
        fromDate: "",
        toDate: "",
        menu: false
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
          toDate: ""
        }
      ];
      this.savedData = {
        individual: undefined,
        profile: undefined,
        enrollments: undefined
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
          this.profileForm.username === "" ? null : this.profileForm.username
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
        isBot: this.profileForm.isBot
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
          this.enrollmentsForm.map(enrollment => {
            if (enrollment.organization) {
              const fromDate = enrollment.fromDate
                ? new Date(enrollment.fromDate).toISOString()
                : null;
              const toDate = enrollment.toDate
                ? new Date(enrollment.toDate).toISOString()
                : null;
              const response = this.enroll(
                this.savedData.individual,
                enrollment.organization,
                fromDate,
                toDate
              );
              this.$logger.debug(
                `Enrolled individual ${this.savedData.individual}`,
                {
                  uuid: this.savedData.individual,
                  organization: enrollment.organization,
                  fromDate,
                  toDate
                }
              );
              return response;
            }
          })
        );
        if (response) {
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
    }
  }
};
</script>
