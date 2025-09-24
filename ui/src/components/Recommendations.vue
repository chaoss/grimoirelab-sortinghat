<template>
  <v-dialog v-model="isOpen" width="840" persistent>
    <template v-slot:activator="{ props: dialog }">
      <v-btn-group
        v-show="count !== 0"
        class="mr-4"
        density="comfortable"
        variant="outlined"
        divided
      >
        <v-btn v-bind="dialog" height="34" variant="outlined" size="small">
          <v-icon size="small" start>mdi-lightbulb-on-outline</v-icon>
          Recommendations
          <v-chip class="ml-1" size="x-small">{{ count }}</v-chip>
        </v-btn>
        <v-menu v-model="menu" location="bottom">
          <template v-slot:activator="{ props: menu }">
            <v-btn
              size="small"
              height="34"
              icon="mdi-menu-down"
              aria-label="Open menu"
              v-bind="menu"
            />
          </template>
          <v-list density="comfortable" nav>
            <v-list-item v-bind="dialog">
              <v-list-item-title>Review recommendations</v-list-item-title>
            </v-list-item>
            <v-dialog
              activator="parent"
              aria-label="Delete recommendations confirmation"
              width="500"
            >
              <template v-slot:activator="{ props: activator }">
                <v-list-item v-bind="activator">
                  <v-list-item-title>
                    Delete all recommendations
                  </v-list-item-title>
                </v-list-item>
              </template>
              <template v-slot:default="{ isActive }">
                <v-card
                  title="Delete all recommendations?"
                  :text="errorMessage"
                >
                  <template v-slot:actions>
                    <v-btn
                      class="ml-auto"
                      text="Cancel"
                      @click="isActive.value = false"
                    ></v-btn>
                    <v-btn
                      color="primary"
                      text="Delete"
                      variant="flat"
                      @click="deleteRecommendations(isActive)"
                    ></v-btn>
                  </template>
                </v-card>
              </template>
            </v-dialog>
          </v-list>
        </v-menu>
      </v-btn-group>
    </template>

    <v-card v-if="currentItem" class="section">
      <v-card-title class="header title d-flex justify-space-between">
        <span>Review recommendations</span>
        <v-btn
          icon="mdi-close"
          color="primary"
          class="mr-n2"
          variant="text"
          @click="onClose"
        >
        </v-btn>
      </v-card-title>
      <v-card-subtitle
        class="mt-4 pl-8 pr-8 pb-0 text-subtitle-1 d-flex justify-space-between"
      >
        Select which identities to merge and which to keep separate
        <span class="subtitle-1 text--secondary">{{ count }} remaining</span>
      </v-card-subtitle>
      <v-card-text class="mt-4 pl-8 pr-8">
        <v-row class="flex-nowrap" no-gutters>
          <v-col>
            <individual-card
              :name="currentItem.individual1.name"
              :email="currentItem.individual1.email"
              :sources="currentItem.individual1.sources"
              :uuid="currentItem.individual1.uuid"
              :identities="currentItem.individual1.identities"
              :enrollments="currentItem.individual1.enrollments"
              :is-locked="currentItem.individual1.isLocked"
              :emails="currentItem.individual1.emails"
              :usernames="currentItem.individual1.usernames"
              variant="outlined"
              detailed
            />
          </v-col>
          <v-col :cols="1" class="d-flex justify-center align-self-center">
            <v-icon>mdi-arrow-left</v-icon>
          </v-col>
          <v-col>
            <individual-card
              v-for="match in currentItem.matches"
              :key="match.id"
              :name="match.individual.name"
              :email="match.individual.email"
              :sources="match.individual.sources"
              :uuid="match.individual.uuid"
              :identities="match.individual.identities"
              :enrollments="match.individual.enrollments"
              :is-locked="match.individual.isLocked"
              :is-selected="match.checked"
              :emails="match.individual.emails"
              :usernames="match.individual.usernames"
              class="mb-1"
              variant="outlined"
              detailed
              recommendation
              @check="($event) => (match.checked = $event)"
              @apply="($event) => (match.apply = $event)"
            />
          </v-col>
        </v-row>

        <v-alert v-if="errorMessage" variant="tonal" type="error" class="mt-4">
          {{ errorMessage }}
        </v-alert>

        <v-card-actions class="px-0 mt-4">
          <v-spacer></v-spacer>
          <v-btn
            class="text-subtitle-2"
            color="primary darken-1"
            variant="outlined"
            @click.prevent="fetchItem(page + currentItem.matches.length)"
          >
            Ask again later
          </v-btn>
          <v-btn
            :loading="isLoading"
            class="text-subtitle-2"
            color="primary"
            variant="flat"
            @click.prevent="applyRecommendations(true)"
          >
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { formatIndividual } from "../utils/actions";
import IndividualCard from "./IndividualCard.vue";

export default {
  name: "Recommendations",
  components: { IndividualCard },
  inject: [
    "getRecommendations",
    "getRecommendationsCount",
    "manageRecommendation",
    "deleteMergeRecommendations",
  ],
  data() {
    return {
      count: 0,
      currentItem: null,
      isOpen: false,
      errorMessage: null,
      menu: null,
      page: 1,
      isLoading: false,
    };
  },
  methods: {
    async fetchCount() {
      try {
        const response = await this.getRecommendationsCount();
        this.count = response.data.recommendedMerge.pageInfo.totalResults;
      } catch (error) {
        this.$logger.error(`Error fetching recommendations: ${error}`);
      }
    },
    async fetchItem(page = 1) {
      if (this.currentItem && !this.currentItem.pageInfo.hasNext) {
        return this.onClose();
      }
      this.errorMessage = null;
      try {
        const response = await this.getRecommendations(page, 1);
        if (response.data.recommendedMerge.entities) {
          const recommendation = response.data.recommendedMerge.entities[0];
          this.currentItem = {
            individual1: formatIndividual(recommendation.individual1),
            matches: recommendation.individual1.matchRecommendationSet.map(
              (rec) => ({
                apply: null,
                id: rec.id,
                individual: formatIndividual(rec.individual),
              })
            ),
            pageInfo: response.data.recommendedMerge.pageInfo,
          };
          this.count = this.currentItem.pageInfo.totalResults;
          this.page = this.currentItem.pageInfo.page;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error fetching item: ${error}`);
      }
    },
    async applyRecommendations() {
      const recommendations = this.currentItem.matches.filter(
        (match) => match.apply || match.apply === false
      );
      if (recommendations.length === 0) {
        this.errorMessage = "No action selected";
      }
      try {
        this.isLoading = true;
        for (let recommendation of recommendations) {
          await this.manageRecommendation(
            recommendation.id,
            recommendation.apply
          );
        }
        this.$logger.debug(
          `Managed recommendations`,
          recommendations.map((rec) => rec.id)
        );
        const remaining = this.currentItem.matches.filter(
          (match) => match.apply === null
        );
        if (remaining.length === 0) {
          this.fetchItem(this.page);
        } else if (!this.currentItem.pageInfo.hasNext) {
          this.onClose();
        } else {
          this.currentItem.matches = remaining;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error applying recommendations: ${error}`);
      }
      this.isLoading = false;
    },
    onClose() {
      this.isOpen = false;
      this.currentItem = null;
      this.errorMessage = null;
      this.fetchCount();
      this.$emit("updateTable");
      this.$emit("updateWorkspace");
    },
    async deleteRecommendations(isActive) {
      try {
        await this.deleteMergeRecommendations();
        this.count = 0;
        this.menu = false;
        this.errorMessage = null;
        isActive.value = false;
      } catch (error) {
        this.$logger.error(`Error removing recommendations: ${error}`);
        this.errorMessage = this.$getErrorMessage(error);
      }
    },
  },
  watch: {
    isOpen(value) {
      if (value && this.count > 0) {
        this.fetchItem();
      }
    },
  },
  mounted() {
    this.fetchCount();
  },
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

.col {
  max-width: 290px;
}

.v-btn-group--density-comfortable.v-btn-group {
  height: 34px;
}
</style>
