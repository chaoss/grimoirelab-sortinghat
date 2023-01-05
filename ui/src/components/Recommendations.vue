<template>
  <v-dialog v-model="isOpen" width="700" persistent>
    <template v-slot:activator="{ on }">
      <slot name="activator" :on="on">
        <v-btn
          v-show="count !== 0"
          v-on="on"
          class="mr-4"
          height="34"
          outlined
          small
        >
          <v-icon left small>mdi-lightbulb-on-outline</v-icon>
          {{ count }} recommendation{{ count > 1 ? "s" : "" }}
        </v-btn>
      </slot>
    </template>

    <v-card v-if="currentItem" class="section">
      <v-card-title class="header title d-flex justify-space-between">
        <span>Review recommendations</span>
        <v-btn icon color="primary" class="mr-n2" @click="onClose">
          <v-icon color="primary">mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-subtitle
        class="mt-4 pl-8 pr-8 pb-0 text-subtitle-1 d-flex justify-space-between"
      >
        Is this the same individual?
        <span class="subtitle-1 text--secondary">
          {{ page }} of {{ count }}
        </span>
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
            <v-icon>mdi-arrow-right</v-icon>
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

        <v-alert v-if="errorMessage" text type="error" class="mt-4">
          {{ errorMessage }}
        </v-alert>

        <v-card-actions class="pr-0 mt-4">
          <v-spacer></v-spacer>
          <v-btn
            color="primary darken-1"
            text
            @click.prevent="applyRecommendation(false)"
          >
            Dismiss
          </v-btn>
          <v-btn
            color="primary"
            depressed
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
    "manageRecommendation"
  ],
  data() {
    return {
      count: 0,
      currentItem: null,
      isOpen: false,
      errorMessage: null,
      page: 1
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
    async fetchItem() {
      try {
        const response = await this.getRecommendations(1, 1);
        if (response.data.recommendedMerge.entities) {
          const recommendation = response.data.recommendedMerge.entities[0];
          this.currentItem = {
            individual1: formatIndividual(recommendation.individual1),
            individual2: formatIndividual(recommendation.individual2),
            id: parseInt(recommendation.id),
            pageInfo: response.data.recommendedMerge.pageInfo
          };
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
          this.page++;
          this.fetchItem();
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
      this.page = 1;
      this.fetchCount();
      this.$emit("updateTable");
      this.$emit("updateWorkspace");
    }
  },
  watch: {
    isOpen(value) {
      if (value && this.count > 0) {
        this.fetchItem();
      }
    }
  },
  mounted() {
    this.fetchCount();
  }
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

.col {
  max-width: 290px;
}
</style>
