<template>
  <v-dialog v-model="isOpen" persistent max-width="650">
    <v-card class="pa-6">
      <v-card-title>
        <span class="headline">Add individual</span>
      </v-card-title>
      <v-card-text>
        <v-form ref="form">
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Name"
                :rules="validations.required"
                v-model="profileForm.name"
                filled
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Email"
                v-model="profileForm.email"
                :rules="validations.email"
                filled
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Username"
                v-model="profileForm.username"
                :rules="validations.required"
                filled
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                label="Source"
                v-model="profileForm.source"
                :rules="validations.required"
                filled
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="6">
              <v-text-field
                label="Gender"
                v-model="profileForm.gender"
                filled
              />
            </v-col>
            <v-col cols="4">
              <v-text-field
                label="Country code"
                v-model="profileForm.country"
                filled
              />
            </v-col>
            <v-col cols="2">
              <v-checkbox
                v-model="profileForm.isBot"
                label="Bot"
                color="primary"
              >
              </v-checkbox>
            </v-col>
          </v-row>
        </v-form>

        <v-row class="pl-4">
          <span class="title font-weight-regular pl-16">Organizations</span>
        </v-row>
        <v-row v-for="(enrollment, index) in enrollmentsForm" :key="index">
          <v-col cols="4">
            <v-text-field
              label="Organization"
              v-model="enrollmentsForm[index].organization"
              filled
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              label="Date from"
              v-model="enrollmentsForm[index].fromDate"
              hint="MM/DD/YYYY"
              filled
            />
          </v-col>
          <v-col cols="3">
            <v-text-field
              label="Date to"
              v-model="enrollmentsForm[index].toDate"
              hint="MM/DD/YYYY"
              filled
            />
          </v-col>
          <v-col cols="1" class="pt-6">
            <v-btn
              v-if="index === enrollmentsForm.length - 1"
              icon
              color="primary"
              :disabled="enrollment.length === 0"
              @click="addInput"
            >
              <v-icon color="primary">mdi-plus-circle-outline</v-icon>
            </v-btn>
            <v-btn v-else icon color="primary" @click="removeEnrollment(index)">
              <v-icon color="primary">mdi-delete</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>

      <v-alert v-if="errorMessage" text type="error">
        {{ errorMessage }}
      </v-alert>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="blue darken-1" text @click.prevent="closeModal">
          Cancel
        </v-btn>
        <v-btn depressed color="primary" @click.prevent="onSave">
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
        isBot: false
      },
      enrollmentsForm: [
        {
          organization: "",
          fromDate: "",
          toDate: ""
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
          value => !!value || "Required",
          value => /\S+@\S+\.\S+/.test(value) || "Invalid email"
        ]
      },
      errorMessage: ""
    };
  },
  methods: {
    addInput() {
      this.enrollmentsForm.push({
        organization: "",
        fromDate: "",
        toDate: ""
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
      try {
        const response = await this.addIdentity(
          this.profileForm.email,
          this.profileForm.name,
          this.profileForm.source,
          this.profileForm.username
        );
        if (response && response.data.addIdentity) {
          this.savedData.individual = response.data.addIdentity.uuid;
          return this.savedData.individual;
        }
      } catch (error) {
        this.errorMessage = error;
      }
    },
    async addProfileInfo(uuid) {
      try {
        const data = {
          gender: this.profileForm.gender,
          countryCode: this.profileForm.country,
          isBot: this.profileForm.isBot
        };
        const response = await this.updateProfile(data, uuid);
        if (response && response.data.updateProfile) {
          this.savedData.profile = response.data.updateProfile;
          return this.savedData.profile;
        }
      } catch (error) {
        this.errorMessage = error;
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
              return response;
            }
          })
        );
        if (response) {
          return response;
        }
      } catch (error) {
        this.errorMessage = error;
      }
    }
  }
};
</script>
