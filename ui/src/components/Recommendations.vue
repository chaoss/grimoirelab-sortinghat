<template>
  <v-dialog v-model="isOpen" width="700" persistent>
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
              max-width="500"
              aria-label="Delete recommendations confirmation"
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
        Is this the same individual?
        <span class="subtitle-1 text--secondary">{{ count }} remaining</span>
      </v-card-subtitle>
      <v-card-text class="mt-4 pl-8 pr-8">
        <v-row align="center" class="flex-nowrap" no-gutters>
          <v-col>
            <individual-card
              :name="currentItem.individual1.name"
              :email="currentItem.individual1.email"
              :sources="currentItem.individual1.sources"
              :uuid="currentItem.individual1.uuid"
              :identities="currentItem.individual1.identities"
              :enrollments="currentItem.individual1.enrollments"
              :is-locked="currentItem.individual1.isLocked"
            />
          </v-col>
          <v-col :cols="1" class="d-flex justify-center">
            <v-icon>mdi-arrow-left</v-icon>
          </v-col>
          <v-col>
            <individual-card
              :name="currentItem.individual2.name"
              :email="currentItem.individual2.email"
              :sources="currentItem.individual2.sources"
              :uuid="currentItem.individual2.uuid"
              :identities="currentItem.individual2.identities"
              :enrollments="currentItem.individual2.enrollments"
              :is-locked="currentItem.individual2.isLocked"
            />
          </v-col>
        </v-row>

        <v-alert v-if="errorMessage" variant="tonal" type="error" class="mt-4">
          {{ errorMessage }}
        </v-alert>

        <v-card-actions class="px-0 mt-4">
          <v-btn
            color="primary darken-1"
            variant="text"
            @click.prevent="fetchItem(page + 1)"
          >
            Skip
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary darken-1"
            variant="text"
            @click.prevent="applyRecommendation(false)"
          >
            Dismiss
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click.prevent="applyRecommendation(true)"
          >
            Merge
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
      try {
        const response = await this.getRecommendations(page, 1);
        if (response.data.recommendedMerge.entities) {
          const recommendation = response.data.recommendedMerge.entities[0];
          this.currentItem = {
            individual1: formatIndividual(recommendation.individual1),
            individual2: formatIndividual(recommendation.individual2),
            id: parseInt(recommendation.id),
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
    async applyRecommendation(apply) {
      this.errorMessage = null;
      try {
        await this.manageRecommendation(this.currentItem.id, apply);
        this.$logger.debug(
          `${apply ? "Applied" : "Dismissed"} recommendation ${
            this.currentItem.id
          }`
        );
        if (!this.currentItem.pageInfo.hasNext) {
          this.onClose();
        } else {
          this.fetchItem(this.page);
        }
      } catch (error) {
        this.errorMessage = this.$getErrorMessage(error);
        this.$logger.error(
          `Error applying recommendation ${this.currentItem.id}: ${error}`
        );
      }
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
