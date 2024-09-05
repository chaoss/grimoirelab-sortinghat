<template>
  <v-main>
    <loading-spinner v-if="$apollo.loading" label="Loading" />
    <v-container v-else-if="individual" class="mx-auto mb-8">
      <v-row>
        <v-col
          :cols="showRecommendations ? 8 : 12"
          :xl="showRecommendations ? 9 : 12"
        >
          <v-row class="section pa-3 mb-4 mt-0">
            <v-col>
              <v-list-item class="pl-1 my-n4 v-list-item--three-line">
                <template v-slot:prepend>
                  <avatar :name="individual.name" :email="individual.email" />
                </template>

                <v-list-item-title class="font-weight-medium text-h6">
                  <span v-if="individual.isLocked">
                    {{ individual.name || "no name" }}
                  </span>
                  <edit-dialog
                    v-else
                    v-model="individual.name"
                    empty-value="no name"
                    label="Edit name"
                    @save="updateProfile({ name: $event })"
                  />
                </v-list-item-title>
                <v-list-item-subtitle class="mb-1">
                  {{ individual.organization }}
                </v-list-item-subtitle>
                <p
                  v-for="(profile, i) in socialProfiles"
                  :key="i"
                  class="d-flex align-center"
                >
                  <v-icon size="small" start>{{ profile.icon }}</v-icon>
                  <a
                    :href="profile.link"
                    :data-profile-link="profile.source"
                    class="link--underline font-weight-regular"
                    target="_blank"
                  >
                    {{ profile.username }}
                  </a>
                </p>
              </v-list-item>
            </v-col>

            <v-col cols="2" class="d-flex justify-end align-start mr-1">
              <v-tooltip location="bottom" max-width="200">
                <template v-slot:activator="{ props }">
                  <v-btn
                    :disabled="individual.isLocked"
                    :aria-label="reviewButton.tooltip"
                    :icon="reviewButton.icon"
                    v-bind="props"
                    class="mr-1"
                    data-testid="review-btn"
                    variant="text"
                    @click="review(this.mk)"
                  >
                  </v-btn>
                </template>
                <span>
                  {{ reviewButton.tooltip }}
                </span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn
                    :disabled="individual.isLocked"
                    :aria-label="
                      individual.isBot ? 'Unmark as bot' : 'Mark as bot'
                    "
                    :icon="individual.isBot ? 'mdi-robot' : 'mdi-robot-outline'"
                    v-bind="props"
                    class="mr-1"
                    variant="text"
                    @click="updateProfile({ isBot: !individual.isBot })"
                  >
                  </v-btn>
                </template>
                <span>
                  {{ individual.isBot ? "Unmark as bot" : "Mark as bot" }}
                </span>
              </v-tooltip>
              <v-tooltip location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn
                    :aria-label="
                      isInWorkspace ? 'In workspace' : 'Add to workspace'
                    "
                    class="mr-1"
                    variant="text"
                    v-bind="props"
                    :icon="isInWorkspace ? 'mdi-pin' : 'mdi-pin-outline'"
                    @click="$store.dispatch('togglePin', mk)"
                  >
                  </v-btn>
                </template>
                <span>
                  {{ isInWorkspace ? "In workspace" : "Add to workspace" }}
                </span>
              </v-tooltip>
              <v-tooltip v-if="individual.isLocked" location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn
                    aria-label="Unlock"
                    class="mr-1"
                    v-bind="props"
                    icon="mdi-lock"
                    variant="text"
                    @click="unlock"
                  >
                  </v-btn>
                </template>
                <span>Unlock</span>
              </v-tooltip>
              <v-tooltip v-else location="bottom">
                <template v-slot:activator="{ props }">
                  <v-btn
                    aria-label="Lock"
                    class="mr-1"
                    v-bind="props"
                    icon="mdi-lock-outline"
                    variant="text"
                    @click="lock"
                  >
                  </v-btn>
                </template>
                <span>Lock</span>
              </v-tooltip>
              <v-menu location="bottom" left nudge-bottom="38">
                <template v-slot:activator="{ props }">
                  <v-btn
                    aria-label="See more actions"
                    v-bind="props"
                    icon="mdi-dots-vertical"
                    variant="text"
                  >
                  </v-btn>
                </template>
                <v-list density="compact">
                  <v-list-item
                    :disabled="individual.isLocked"
                    @click="matchesModal.open = true"
                  >
                    <v-list-item-title>Find matches</v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-if="hasLinkedinProfile"
                    :disabled="individual.isLocked"
                    @click="confirmRemoveIdentity"
                  >
                    <v-list-item-title>
                      Remove LinkedIn profile
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-else
                    :disabled="individual.isLocked"
                    @click="linkedinModal.open = true"
                  >
                    <v-list-item-title>Add LinkedIn profile</v-list-item-title>
                  </v-list-item>
                  <v-divider inline></v-divider>
                  <v-list-item
                    :disabled="individual.isLocked"
                    @click="confirmDelete"
                  >
                    <v-list-item-title>Delete individual</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </v-col>
          </v-row>

          <v-row class="section mb-4">
            <v-container class="pb-6" fluid>
              <v-list-subheader class="text-subtitle-2 mb-4"
                >Profile</v-list-subheader
              >
              <v-row>
                <v-col cols="1" class="ml-4"> Email: </v-col>
                <v-col>
                  <span v-if="individual.isLocked">
                    {{ individual.email || "none" }}</span
                  >
                  <edit-dialog
                    v-else
                    v-model="individual.email"
                    empty-value="none"
                    label="Edit email"
                    @save="updateProfile({ email: $event })"
                  />
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="1" class="ml-4"> Country: </v-col>
                <v-col>
                  <span v-if="individual.isLocked">
                    {{ individual.country ? individual.country.name : "none" }}
                  </span>
                  <edit-dialog
                    v-else
                    v-model="individual.country"
                    empty-value="none"
                    label="Edit country"
                    @save="updateProfile({ countryCode: $event.code })"
                  >
                    <template v-slot:value="{ props }">
                      <span v-bind="props">{{ individual.country.name }}</span>
                    </template>
                    <template v-slot:input="{ model }">
                      <v-combobox
                        v-model="model.value"
                        :items="countries"
                        label="Country"
                        item-title="name"
                        hide-details
                        single-line
                        @click.once="getCountryList"
                        @keypress.once="getCountryList"
                      />
                    </template>
                  </edit-dialog>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="1" class="ml-4"> Gender: </v-col>
                <v-col>
                  <span v-if="individual.isLocked">
                    {{ individual.gender || "none" }}
                  </span>
                  <edit-dialog
                    v-else
                    v-model="individual.gender"
                    empty-value="none"
                    label="Edit gender"
                    @save="updateProfile({ gender: $event })"
                  />
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="1" class="ml-4">
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
                @openEnrollmentModal="confirmEnroll(individual)"
                @openTeamModal="openTeamModal"
                @updateEnrollment="updateEnrollment"
                @withdraw="withdraw"
              />
            </v-container>
          </v-row>
        </v-col>
        <v-col cols="4" v-if="showRecommendations" xl="3">
          <v-container class="section">
            <v-list-subheader class="text-subtitle-2">
              Possible matches
            </v-list-subheader>
            <div
              v-for="(
                { id, individual }, index
              ) in individual.matchRecommendations"
              :key="id"
              class="ml-2 mr-2"
            >
              <individual-card
                :name="individual.name"
                :email="individual.email"
                :enrollments="individual.enrollments"
                :identities="individual.identities"
                :is-locked="individual.isLocked"
                :sources="individual.sources"
                :uuid="individual.uuid"
                :class="{ 'mt-4': index > 0, 'mt-2': index === 0 }"
              />
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  variant="text"
                  size="small"
                  @click.prevent="applyRecommendation(id, false)"
                >
                  Dismiss
                </v-btn>
                <v-btn
                  size="small"
                  variant="outlined"
                  @click.prevent="applyRecommendation(id, true)"
                >
                  Merge
                </v-btn>
              </v-card-actions>
            </div>
          </v-container>
        </v-col>
      </v-row>
    </v-container>

    <v-container v-if="error">
      <v-alert dense text type="error"> Individual {{ error }} </v-alert>
      <v-btn to="/" color="primary" depressed>
        <v-icon left dark>mdi-arrow-left</v-icon>
        Go to dashboard
      </v-btn>
    </v-container>

    <enroll-modal
      v-model:is-open="enrollmentModal.open"
      :title="enrollmentModal.title"
      :text="enrollmentModal.text"
      :uuid="mk"
      :enroll="enrollIndividual"
      :fetch-organizations="fetchOrganizations"
      :add-organization="addOrganization"
    />

    <team-enroll-modal
      v-if="teamModal.open"
      v-model:is-open="teamModal.open"
      :organization="teamModal.organization"
      :uuid="mk"
      :enroll="enroll"
      :enrollments="individual.enrollments"
      @updateIndividual="updateIndividual($event)"
    />

    <matches-modal
      v-model:is-open="matchesModal.open"
      :recommend-matches="recommendMatches"
      :uuid="mk"
    />

    <v-dialog v-model="linkedinModal.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">Add LinkedIn profile</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="linkedinModal.username"
            label="LinkedIn username"
            prefix="https://www.linkedin.com/in/"
            placeholder="username"
            autofocus
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="linkedinModal.open = false"> Cancel </v-btn>
          <v-btn
            :disabled="!linkedinModal.username"
            color="primary"
            @click.stop="addLinkedInProfile"
          >
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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
          <v-btn text @click="closeDialog"> Cancel </v-btn>
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
          <v-btn text color="primary" @click="closeDialog"> OK </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-main>
</template>

<script>
import dayjs from "dayjs";
import {
  getCountries,
  findOrganization,
  GET_INDIVIDUAL_BYUUID,
} from "../apollo/queries";
import {
  addLinkedinProfile,
  deleteIdentity,
  enroll,
  lockIndividual,
  manageMergeRecommendation,
  unlockIndividual,
  unmerge,
  updateEnrollment,
  updateProfile,
  withdraw,
  recommendMatches,
  reviewIndidivual,
} from "../apollo/mutations";
import { formatIndividual } from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import Avatar from "../components/Avatar.vue";
import IdentitiesList from "../components/IdentitiesList.vue";
import IndividualCard from "../components/IndividualCard.vue";
import EnrollmentList from "../components/EnrollmentList.vue";
import EnrollModal from "../components/EnrollModal.vue";
import TeamEnrollModal from "../components/TeamEnrollModal.vue";
import MatchesModal from "../components/MatchesModal.vue";
import EditDialog from "../components/EditDialog.vue";
import LoadingSpinner from "../components/LoadingSpinner.vue";

export default {
  name: "Individual",
  components: {
    Avatar,
    IdentitiesList,
    IndividualCard,
    EnrollmentList,
    EnrollModal,
    TeamEnrollModal,
    MatchesModal,
    EditDialog,
    LoadingSpinner,
  },
  mixins: [enrollMixin],
  apollo: {
    individuals() {
      return {
        query: GET_INDIVIDUAL_BYUUID,
        variables: { uuid: this.mk },
        result(result) {
          if (result.data.individuals.entities.length === 1) {
            this.updateIndividual(result.data.individuals.entities);
          } else if (result.errors) {
            this.error = this.$getErrorMessage(result.errors[0]);
          } else {
            this.error = `Individual ${this.mk} not found`;
          }
        },
      };
    },
  },
  data() {
    return {
      individual: null,
      dialog: {
        open: false,
        title: "",
        text: "",
        errorMessage: "",
        action: null,
      },
      form: {},
      teamModal: {
        open: false,
        organization: "",
      },
      matchesModal: {
        open: false,
      },
      linkedinModal: {
        open: false,
        username: "",
      },
      countries: [],
      socialProfiles: [],
      mk: this.$route.params.mk,
      error: null,
    };
  },
  computed: {
    showRecommendations() {
      return (
        this.individual.matchRecommendations &&
        this.individual.matchRecommendations.length > 0
      );
    },
    isInWorkspace() {
      const workspace = this.$store.getters.workspace;
      return workspace && workspace.indexOf(this.mk) !== -1;
    },
    hasLinkedinProfile() {
      return this.socialProfiles.some(
        (profile) => profile.source === "linkedin"
      );
    },
    reviewButton() {
      const reviewDate = this.$formatDate(
        this.individual.lastReviewed,
        "YYYY-MM-DD"
      );
      const unreviewedChanges = dayjs(this.individual.lastModified).isAfter(
        this.individual.lastReviewed,
        "second"
      );
      if (!reviewDate) {
        return {
          icon: "mdi-check-decagram-outline",
          tooltip: "Mark as reviewed",
        };
      } else if (unreviewedChanges) {
        return {
          icon: "mdi-alert-decagram",
          tooltip: `Changes since last review on ${reviewDate}`,
        };
      } else {
        return {
          icon: "mdi-check-decagram",
          tooltip: `Last reviewed ${reviewDate}`,
        };
      }
    },
  },
  methods: {
    async updateProfile(data) {
      try {
        const response = await updateProfile(this.$apollo, data, this.mk);
        this.updateIndividual(response.data.updateProfile.individual);
        this.$logger.debug(`Updated profile ${this.mk}`, data);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error updating profile: ${error}`, data);
      }
    },
    async lock() {
      try {
        const response = await lockIndividual(this.$apollo, this.mk);
        Object.assign(this.individual, {
          isLocked: response.data.lock.individual.isLocked,
        });
        this.$logger.debug(`Locked individual ${this.mk}`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error locking profile",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error locking individual ${this.mk}: ${error}`);
      }
    },
    async unlock() {
      try {
        const response = await unlockIndividual(this.$apollo, this.mk);
        Object.assign(this.individual, {
          isLocked: response.data.unlock.individual.isLocked,
        });
        this.$logger.debug(`Unlocked individual ${this.mk}`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error),
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
          errorMessage: this.$getErrorMessage(error),
        };
      }
    },
    async unmergeIdentities(uuids) {
      try {
        const response = await unmerge(this.$apollo, uuids);
        const updatedIndividual =
          response.data.unmergeIdentities.individuals.find(
            (individual) => individual.mk === this.mk
          );
        this.updateIndividual(updatedIndividual);
        this.$logger.debug("Unmerged identities", uuids);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error),
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
        this.updateIndividual(response.data.updateEnrollment.individual);
        this.$logger.debug("Updated enrollment", data);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error),
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
        this.updateIndividual(response.data.withdraw.individual);
        this.$logger.debug("Removed affiliation", { uuid: this.mk, ...data });
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error updating profile",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error removing affiliation: ${error}`, {
          uuid: this.mk,
          ...data,
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
          errorMessage: this.$getErrorMessage(error),
        };
      }
    },
    openTeamModal(organization) {
      this.teamModal = {
        open: true,
        organization: organization,
      };
    },
    confirmDelete() {
      this.dialog = {
        open: true,
        title: `Delete ${this.individual.name}?`,
        action: this.deleteIndividual,
      };
    },
    closeDialog() {
      this.dialog = {
        open: false,
        title: "",
        text: "",
        errorMessage: "",
      };
    },
    updateIndividual(newData) {
      if (!Array.isArray(newData)) {
        newData = [newData];
      }

      this.individual = formatIndividual(newData[0]);
      this.socialProfiles = this.getSocialProfiles(newData[0]);

      Object.assign(this.form, {
        name: this.individual.name,
        email: this.individual.email,
        country: this.individual.country,
        gender: this.individual.gender,
      });

      document.title = `${this.individual.name || "Individual"} - Sorting Hat`;
    },
    async fetchOrganizations(page, items, filters) {
      const response = await findOrganization(
        this.$apollo,
        page,
        items,
        filters
      );
      return response.data.organizations;
    },
    async applyRecommendation(id, apply) {
      try {
        await manageMergeRecommendation(this.$apollo, id, apply);
        this.$apollo.queries.individuals.refetch();
        this.$logger.debug(`Applied recommendation ${id}`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error applying recommendation",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error applying recommendation ${id}: ${error}`);
      }
    },
    async recommendMatches(criteria, exclude, strict, uuid) {
      const response = await recommendMatches(
        this.$apollo,
        criteria,
        exclude,
        strict,
        uuid
      );
      return response;
    },
    getSocialProfiles(individual) {
      return individual.identities.reduce((result, identity) => {
        const linkedSources = [
          {
            source: "github",
            link: `http://github.com/${identity.username}`,
            icon: "mdi-github",
          },
          {
            source: "linkedin",
            link: `https://www.linkedin.com/in/${identity.username}`,
            icon: "mdi-linkedin",
          },
        ];
        const socialProfile = linkedSources.find(
          (item) => item.source === identity.source.toLowerCase()
        );

        const isDuplicated = result.find(
          (profile) =>
            profile.source === identity.source &&
            profile.username === identity.username
        );

        if (socialProfile && !isDuplicated) {
          result.push({ ...identity, ...socialProfile });
        }

        return result;
      }, []);
    },
    async addLinkedInProfile() {
      try {
        const response = await addLinkedinProfile(
          this.$apollo,
          this.mk,
          this.linkedinModal.username
        );
        this.updateIndividual(response.data.addIdentity.individual);
        Object.assign(this.linkedinModal, { open: false, username: "" });
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error adding identity",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error adding identity: ${error}`);
      }
    },
    async removeLinkedInProfile() {
      try {
        const uuid = this.socialProfiles.find(
          (identity) => identity.source === "linkedin"
        )?.uuid;
        const response = await deleteIdentity(this.$apollo, uuid);
        this.updateIndividual(response.data.deleteIdentity.individual);
        this.closeDialog();
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error removing identity",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error removing identity: ${error}`);
      }
    },
    confirmRemoveIdentity() {
      this.dialog = {
        open: true,
        title: "Remove LinkedIn profile?",
        action: this.removeLinkedInProfile,
      };
    },
    async review(uuid) {
      try {
        const response = await reviewIndidivual(this.$apollo, uuid);
        this.updateIndividual(response.data.review.individual);
        this.$logger.debug(`Marked individual ${this.mk} as reviewed`);
      } catch (error) {
        this.dialog = {
          open: true,
          title: "Error reviewing individual",
          errorMessage: this.$getErrorMessage(error),
        };
        this.$logger.error(`Error reviewing individual: ${error}`);
      }
    },
  },
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

.section {
  font-size: 0.875rem;
}

.aligned {
  margin-bottom: 4px;
}

.v-btn--icon .v-icon--dense {
  font-size: 20px;
}
</style>
