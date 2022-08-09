<template>
  <v-main>
    <v-container v-if="individual" class="ml-auto mr-auto mb-8">
      <v-row>
        <v-col :cols="recommendations.length === 0 ? 12 : 9">
          <v-row class="section pa-3 mb-4">
            <v-col>
              <v-list-item class="pl-1">
                <avatar :name="individual.name" :email="individual.email" />

                <v-list-item-content>
                  <v-list-item-title class="font-weight-medium text-h6">
                    <span v-if="individual.isLocked">{{
                      individual.name
                    }}</span>
                    <v-edit-dialog
                      v-else
                      large
                      @save="updateProfile({ name: form.name })"
                      @cancel="form.name = individual.name"
                    >
                      <button>
                        {{ individual.name || "no name" }}
                        <v-icon
                          class="icon--hidden aligned"
                          aria-label="Edit name"
                          small
                        >
                          mdi-lead-pencil
                        </v-icon>
                      </button>
                      <template v-slot:input>
                        <v-text-field
                          v-model="form.name"
                          label="Edit name"
                          maxlength="30"
                          single-line
                        ></v-text-field>
                      </template>
                    </v-edit-dialog>

                    <v-tooltip
                      bottom
                      transition="expand-y-transition"
                      open-delay="200"
                    >
                      <template v-slot:activator="{ on }">
                        <v-btn
                          v-show="!individual.isLocked"
                          v-on="on"
                          class="aligned focusable"
                          icon
                          small
                          @click="updateProfile({ isBot: !individual.isBot })"
                        >
                          <v-icon
                            :class="{ 'icon--hidden': !individual.isBot }"
                            small
                          >
                            mdi-robot
                          </v-icon>
                        </v-btn>
                      </template>
                      <span>{{
                        individual.isBot ? "Unmark as bot" : "Mark as bot"
                      }}</span>
                    </v-tooltip>
                    <v-icon
                      v-show="individual.isLocked && individual.isBot"
                      class="aligned"
                      small
                      right
                    >
                      mdi-robot
                    </v-icon>
                  </v-list-item-title>
                  <v-list-item-subtitle>{{
                    individual.organization
                  }}</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-col>

            <v-col cols="2" class="d-flex justify-end align-center mr-1">
              <v-btn
                v-if="individual.isLocked"
                class="mr-4"
                text
                small
                outlined
                @click="unlock"
              >
                <v-icon small left>mdi-lock-open</v-icon>
                Unlock
              </v-btn>
              <v-btn v-else class="mr-4" text small outlined @click="lock">
                <v-icon small left>mdi-lock</v-icon>
                Lock
              </v-btn>
              <v-btn
                text
                small
                outlined
                :disabled="individual.isLocked"
                @click="confirmDelete"
              >
                <v-icon small left>mdi-delete</v-icon>
                Delete
              </v-btn>
            </v-col>
          </v-row>

          <v-row class="section mb-4">
            <v-container fluid>
              <v-subheader>Profile</v-subheader>
              <v-row class="ml-9">
                <v-col cols="1" class="ml-6">
                  Email:
                </v-col>
                <v-col>
                  <span v-if="individual.isLocked">{{
                    individual.email || "none"
                  }}</span>
                  <v-edit-dialog
                    v-else
                    large
                    @save="updateProfile({ email: form.email })"
                    @cancel="form.email = individual.email"
                  >
                    <button>
                      {{ individual.email || "none" }}
                      <v-icon
                        class="icon--hidden aligned"
                        aria-label="Edit name"
                        small
                      >
                        mdi-lead-pencil
                      </v-icon>
                    </button>
                    <template v-slot:input>
                      <v-text-field
                        v-model="form.email"
                        label="Edit email"
                        maxlength="30"
                        single-line
                      ></v-text-field>
                    </template>
                  </v-edit-dialog>
                </v-col>
              </v-row>
              <v-row class="ml-9">
                <v-col cols="1" class="ml-6">
                  Country:
                </v-col>
                <v-col>
                  <span v-if="individual.isLocked">
                    {{ individual.country ? individual.country.name : "none" }}
                  </span>
                  <v-edit-dialog
                    v-else
                    large
                    @save="
                      updateProfile({
                        countryCode: form.country ? form.country.code : ''
                      })
                    "
                    @cancel="form.country = individual.country"
                  >
                    <button>
                      {{
                        individual.country ? individual.country.name : "none"
                      }}
                      <v-icon
                        class="icon--hidden aligned"
                        aria-label="Edit country"
                        small
                      >
                        mdi-lead-pencil
                      </v-icon>
                    </button>
                    <template v-slot:input>
                      <v-combobox
                        v-model="form.country"
                        :items="countries"
                        label="Country"
                        item-text="name"
                        single-line
                        @click.once="getCountryList"
                        @keypress.once="getCountryList"
                      />
                    </template>
                  </v-edit-dialog>
                </v-col>
              </v-row>
              <v-row class="ml-9">
                <v-col cols="1" class="ml-6">
                  Gender:
                </v-col>
                <v-col>
                  <span v-if="individual.isLocked">
                    {{ individual.gender || "none" }}
                  </span>
                  <v-edit-dialog
                    v-else
                    large
                    @save="updateProfile({ gender: form.gender })"
                    @cancel="form.gender = individual.gender"
                  >
                    <button>
                      {{ individual.gender || "none" }}
                      <v-icon
                        class="icon--hidden aligned"
                        aria-label="Edit gender"
                        small
                      >
                        mdi-lead-pencil
                      </v-icon>
                    </button>
                    <template v-slot:input>
                      <v-text-field
                        v-model="form.gender"
                        label="Edit gender"
                        maxlength="30"
                        single-line
                      ></v-text-field>
                    </template>
                  </v-edit-dialog>
                </v-col>
              </v-row>
              <v-row class="ml-9">
                <v-col cols="1" class="ml-6">
                  <span>UUID:</span>
                </v-col>
                <v-col>
                  <span>{{ individual.uuid }}</span>
                </v-col>
              </v-row>
            </v-container>
          </v-row>

          <v-row class="section mb-4">
            <v-container fluid>
              <identities-list
                class="mb-8"
                v-if="individual.identities"
                :identities="individual.identities"
                :uuid="individual.uuid"
                :is-locked="individual.isLocked"
                @unmerge="unmergeIdentities"
              />
            </v-container>
          </v-row>

          <v-row class="section">
            <v-container fluid>
              <enrollment-list
                v-if="individual.enrollments"
                :enrollments="individual.enrollments"
                :is-locked="individual.isLocked"
                @openEnrollmentModal="confirmEnroll"
                @openTeamModal="openTeamModal"
                @updateEnrollment="updateEnrollment"
                @withdraw="withdraw"
              />
            </v-container>
          </v-row>
        </v-col>
        <v-col cols="3" v-if="recommendations.length !== 0">
          <v-container class="section"> </v-container>
        </v-col>
      </v-row>
    </v-container>

    <v-container v-else>
      <v-alert dense text type="error"> Individual {{ mk }} not found </v-alert>
      <v-btn to="/" color="primary" depressed>
        <v-icon left dark>mdi-arrow-left</v-icon>
        Go to dashboard
      </v-btn>
    </v-container>

    <enroll-modal
      :is-open.sync="enrollmentModal.open"
      :title="enrollmentModal.title"
      :text="enrollmentModal.text"
      :uuid="mk"
      :enroll="enrollIndividual"
    />

    <team-enroll-modal
      v-if="teamModal.open"
      :is-open.sync="teamModal.open"
      :organization="teamModal.organization"
      :uuid="mk"
      :enroll="enroll"
      @updateTable="fetchIndividual"
    />

    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p v-if="dialog.text" class="pt-2 pb-2 text-body-2">
            {{ dialog.text }}
          </p>
          <v-alert v-if="dialog.errorMessage" dense text type="error">
            {{ dialog.errorMessage }}
          </v-alert>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            id="confirm"
            depressed
            @click.stop="dialog.action"
          >
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-main>
</template>

<script>
import { getCountries, getIndividualByUuid } from "../apollo/queries";
import {
  deleteIdentity,
  enroll,
  lockIndividual,
  unlockIndividual,
  unmerge,
  updateEnrollment,
  updateProfile,
  withdraw
} from "../apollo/mutations";
import { formatIndividuals } from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import Avatar from "../components/Avatar.vue";
import IdentitiesList from "../components/IdentitiesList.vue";
import EnrollmentList from "../components/EnrollmentList.vue";
import EnrollModal from "../components/EnrollModal.vue";
import TeamEnrollModal from "../components/TeamEnrollModal.vue";

export default {
  name: "Individual",
  components: {
    Avatar,
    IdentitiesList,
    EnrollmentList,
    EnrollModal,
    TeamEnrollModal
  },
  mixins: [enrollMixin],
  data() {
    return {
      individual: {},
      recommendations: [],
      form: {
        name: "",
        email: "",
        country: "",
        gender: ""
      },
      dialog: {
        open: false,
        title: "",
        text: "",
        errorMessage: "",
        action: null
      },
      teamModal: {
        open: false,
        organization: ""
      },
      countries: []
    };
  },
  computed: {
    mk() {
      return this.$route.params.mk;
    }
  },
  methods: {
    async fetchIndividual() {
      try {
        const response = await getIndividualByUuid(this.$apollo, this.mk);

        if (response.data.individuals.entities.length === 0) {
          this.individual = false;
          return;
        }

        this.individual = formatIndividuals(
          response.data.individuals.entities
        )[0];

        Object.assign(this.form, {
          name: this.individual.name,
          email: this.individual.email,
          country: this.individual.country,
          gender: this.individual.gender
        });

        document.title = `${this.individual.name} - Sorting Hat`;
      } catch (error) {
        console.log(error);
      }
    },
    async updateProfile(data) {
      try {
        const response = await updateProfile(this.$apollo, data, this.mk);
        this.individual = formatIndividuals([
          response.data.updateProfile.individual
        ])[0];
        this.$logger.debug(`Updated profile ${this.mk}`, data);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error updating profile: ${error}`, data);
      }
    },
    async lock() {
      try {
        const response = await lockIndividual(this.$apollo, this.mk);
        Object.assign(this.individual, {
          isLocked: response.data.lock.individual.isLocked
        });
        this.$logger.debug(`Locked individual ${this.mk}`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error locking profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error locking individual ${this.mk}: ${error}`);
      }
    },
    async unlock() {
      try {
        const response = await unlockIndividual(this.$apollo, this.mk);
        Object.assign(this.individual, {
          isLocked: response.data.unlock.individual.isLocked
        });
        this.$logger.debug(`Unlocked individual ${this.mk}`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error unlocking individual ${this.mk}: ${error}`);
      }
    },
    async getCountryList() {
      try {
        const response = await getCountries(this.$apollo);
        this.countries = response.data.countries.entities;
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error loading country list",
          errorMessage: this.$getErrorMessage(error)
        };
      }
    },
    async unmergeIdentities(uuids) {
      try {
        const response = await unmerge(this.$apollo, uuids);
        const updatedIndividual = response.data.unmergeIdentities.individuals.find(
          individual => individual.mk === this.mk
        );
        this.individual = formatIndividuals([updatedIndividual])[0];
        this.$logger.debug("Unmerged identities", uuids);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error unmerging identities ${uuids}: ${error}`);
      }
    },
    async enroll(uuid, group, fromDate, toDate, parentOrg) {
      const response = await enroll(
        this.$apollo,
        uuid,
        group,
        fromDate,
        toDate,
        parentOrg
      );

      return response;
    },
    async updateEnrollment(data) {
      Object.assign(data, { uuid: this.mk });
      try {
        const response = await updateEnrollment(this.$apollo, data);
        this.individual = formatIndividuals([
          response.data.updateEnrollment.individual
        ])[0];
        this.$logger.debug("Updated enrollment", data);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error updating enrollment: ${error}`, data);
      }
    },
    async withdraw(data) {
      const { name, fromDate, toDate, parentOrg } = data;
      try {
        const response = await withdraw(
          this.$apollo,
          this.mk,
          name,
          fromDate,
          toDate,
          parentOrg
        );
        this.individual = formatIndividuals([
          response.data.withdraw.individual
        ])[0];
        this.$logger.debug("Removed affiliation", { uuid: this.mk, ...data });
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error)
        };
        this.$logger.error(`Error removing affiliation: ${error}`, {
          uuid: this.mk,
          ...data
        });
      }
    },
    async deleteIndividual() {
      try {
        const response = await deleteIdentity(this.$apollo, this.mk);
        if (response) {
          this.$router.push("/");
        }
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error deleting profile",
          errorMessage: this.$getErrorMessage(error)
        };
      }
    },
    openTeamModal(organization) {
      this.teamModal = {
        open: true,
        organization: organization
      };
    },
    confirmDelete() {
      this.dialog = {
        open: true,
        title: `Delete ${this.individual.name}?`,
        action: this.deleteIndividual
      };
    },
    closeDialog() {
      this.dialog = {
        open: false,
        title: "",
        text: "",
        errorMessage: ""
      };
    }
  },
  mounted() {
    this.fetchIndividual();
  }
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

.section {
  font-size: 0.875rem;
}

::v-deep .v-small-dialog__activator,
.v-small-dialog {
  display: inline-block;
}
.v-small-dialog__activator {
  .v-icon {
    opacity: 0;
    padding-bottom: 2px;
  }

  button:focus,
  button:focus-visible {
    background: #f4f4f4;
    .v-icon {
      opacity: 1;
    }
  }

  &:hover {
    .v-icon {
      opacity: 1;
    }
  }
}
.v-list-item__title {
  ::v-deep .icon--hidden {
    opacity: 0;
    padding-bottom: 2px;
  }
  &:hover {
    ::v-deep .icon--hidden {
      opacity: 1;
    }
  }
}

.aligned {
  margin-bottom: 4px;
}
</style>
