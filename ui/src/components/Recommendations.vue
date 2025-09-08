<template>
  <div class="d-inline">
    <v-navigation-drawer
      v-model="isOpen"
      location="right"
      temporary
      width="800"
      elevation="2"
      persistent
    >
      <v-card-title class="header title d-flex justify-space-between">
        <span class="pt-1">Review recommendations</span>
        <v-btn
          icon="mdi-close"
          color="primary"
          class="mr-n2"
          variant="text"
          @click="onClose"
        >
        </v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-alert v-if="errorMessage" variant="tonal" type="error" class="mt-4">
        {{ errorMessage }}
      </v-alert>
      <v-sheet
        v-for="[key, value] in groupedMatches"
        :key="key"
        class="ma-4 pa-0 border"
      >
        <v-row class="flex-nowrap ma-1" no-gutters>
          <v-col>
            <individual-card
              :name="value[0].individual1.name"
              :email="value[0].individual1.email"
              :sources="value[0].individual1.sources"
              :uuid="value[0].individual1.uuid"
              :identities="value[0].individual1.identities"
              :enrollments="value[0].individual1.enrollments"
              :is-locked="value[0].individual1.isLocked"
              :emails="value[0].individual1.emails"
              :usernames="value[0].individual1.usernames"
              variant="text"
              detailed
            ></individual-card>
          </v-col>
          <v-col>
            <individual-card
              v-for="match in value"
              :key="match.individual2.uuid"
              :name="match.individual2.name"
              :email="match.individual2.email"
              :sources="match.individual2.sources"
              :uuid="match.individual2.uuid"
              :identities="match.individual2.identities"
              :enrollments="match.individual2.enrollments"
              :is-locked="match.individual2.isLocked"
              :is-selected="match.checked"
              :emails="match.individual2.emails"
              :usernames="match.individual2.usernames"
              @check="($event) => (match.checked = $event)"
              variant="text"
              checkbox
              detailed
            ></individual-card>
          </v-col>
        </v-row>
        <div class="d-flex pa-4 pt-0 justify-end">
          <v-btn
            class="text-subtitle-2 mr-2"
            color="primary darken-1"
            variant="text"
            @click.prevent="applyRecommendations(key, false)"
          >
            Keep separate
          </v-btn>
          <v-btn
            class="text-subtitle-2"
            color="primary"
            variant="tonal"
            @click.prevent="applyRecommendations(key, true)"
          >
            Merge
          </v-btn>
        </div>
      </v-sheet>
      <template v-slot:append>
        <div class="d-flex pa-4 justify-space-between border">
          <v-pagination
            :model-value="page"
            :length="pages"
            :total-visible="7"
            density="compact"
            @update:modelValue="fetchItems($event)"
          ></v-pagination>
          <div>
            <v-dialog
              activator="parent"
              aria-label="Delete recommendations confirmation"
              width="500"
            >
              <template v-slot:activator="{ props: activator }">
                <v-btn
                  v-bind="activator"
                  class="text-subtitle-2 mr-2 border"
                  color="error darken-1"
                  variant="text"
                  size="large"
                >
                  Delete all
                </v-btn>
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
                      color="error"
                      text="Delete"
                      variant="flat"
                      @click="deleteRecommendations(isActive)"
                    ></v-btn>
                  </template>
                </v-card>
              </template>
            </v-dialog>
          </div>
        </div>
      </template>
    </v-navigation-drawer>
    <v-btn
      v-show="count !== 0"
      @click="isOpen = true"
      height="34"
      variant="outlined"
      size="small"
      class="mr-4"
    >
      <v-icon size="small" start>mdi-lightbulb-on-outline</v-icon>
      Recommendations
      <v-chip class="ml-1" size="x-small">{{ count }}</v-chip>
    </v-btn>
  </div>
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
      isOpen: false,
      errorMessage: null,
      page: 1,
      pages: 1,
      groupedMatches: null,
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
    async fetchItems(page = 1) {
      try {
        const response = await this.getRecommendations(page, 5);
        if (response.data.recommendedMerge.entities) {
          const matches = response.data.recommendedMerge.entities.map(
            (recommendation) => {
              return {
                individual1: formatIndividual(recommendation.individual1),
                individual2: formatIndividual(recommendation.individual2),
                id: parseInt(recommendation.id),
                checked: true,
              };
            }
          );
          this.groupedMatches = Map.groupBy(
            matches,
            ({ individual1 }) => individual1.uuid
          );
          this.count = response.data.recommendedMerge.pageInfo.totalResults;
          this.page = response.data.recommendedMerge.pageInfo.page;
          this.pages = response.data.recommendedMerge.pageInfo.numPages;
          this.errorMessage = null;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error fetching items: ${error}`);
      }
    },
    async applyRecommendations(individualID, apply) {
      const recommendations = this.groupedMatches
        .get(individualID)
        .filter((match) => match.checked);
      try {
        const response = await Promise.all(
          recommendations.map((recommendation) =>
            this.manageRecommendation(recommendation.id, apply)
          )
        );
        if (response) {
          this.$logger.debug(
            `${apply ? "Applied" : "Dismissed"} recommendations`,
            recommendations.map((rec) => rec.id)
          );
          this.fetchItems(this.page);
          this.errorMessage = null;
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(`Error applying recommendations: ${error}`);
      }
    },
    onClose() {
      this.isOpen = false;
      this.errorMessage = null;
      this.fetchCount();
      this.$emit("updateTable");
      this.$emit("updateWorkspace");
    },
    async deleteRecommendations(isActive) {
      try {
        await this.deleteMergeRecommendations();
        this.count = 0;
        this.isOpen = false;
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
        this.fetchItems();
      }
    },
  },
  mounted() {
    this.fetchCount();
  },
};
</script>
