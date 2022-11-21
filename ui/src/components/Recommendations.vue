<template>
  <v-dialog v-model="isOpen" width="700" persistent>
    <template v-slot:activator="{ on }">
      <slot name="activator" :on="on" :items="items">
        <v-btn v-if="items.length !== 0" v-on="on" height="34" small outlined>
          <v-icon left small>mdi-lightbulb-on-outline</v-icon>
          {{ items.length }} recommendation{{ items.length > 1 ? "s" : "" }}
        </v-btn>
      </slot>
    </template>

    <v-card class="section">
      <v-card-title class="header title d-flex justify-space-between">
        <span>Review recommendations</span>
        <span class="subtitle-1 text--secondary">
          {{ currentItem + 1 }} of {{ items.length }}
        </span>
      </v-card-title>
      <v-card-subtitle class="mt-4 pl-8 pr-8 pb-0 text-subtitle-1">
        Is this the same individual?
      </v-card-subtitle>
      <v-card-text class="mt-4">
        <v-row align="center" class="flex-nowrap" no-gutters>
          <v-col>
            <individual-card
              :name="items[currentItem].from.name"
              :email="items[currentItem].from.email"
              :sources="items[currentItem].from.sources"
              :uuid="items[currentItem].from.uuid"
              :identities="items[currentItem].from.identities"
              :enrollments="items[currentItem].from.enrollments"
              :is-locked="items[currentItem].to.isLocked"
            />
          </v-col>
          <v-col :cols="1" class="d-flex justify-center">
            <v-icon>mdi-arrow-right</v-icon>
          </v-col>
          <v-col>
            <individual-card
              :name="items[currentItem].to.name"
              :email="items[currentItem].to.email"
              :sources="items[currentItem].to.sources"
              :uuid="items[currentItem].to.uuid"
              :identities="items[currentItem].to.identities"
              :enrollments="items[currentItem].to.enrollments"
              :is-locked="items[currentItem].to.isLocked"
            />
          </v-col>
        </v-row>

        <v-alert v-if="errorMessage" text type="error" class="mt-4">
          {{ errorMessage }}
        </v-alert>

        <v-card-actions class="pr-0 mt-4">
          <v-spacer></v-spacer>
          <v-btn color="primary darken-1" text @click.prevent="skip">
            Dismiss
          </v-btn>
          <v-btn depressed color="primary" @click.prevent="onMerge">
            Merge
          </v-btn>
        </v-card-actions>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import IndividualCard from "./IndividualCard.vue";

export default {
  name: "Recommendations",
  components: { IndividualCard },
  props: {
    items: {
      type: Array,
      required: true
    },
    mergeItems: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      isOpen: false,
      currentItem: 0,
      errorMessage: null
    };
  },
  methods: {
    async onMerge() {
      try {
        const fromUuids = [this.items[this.currentItem].from.uuid];
        const toUuid = this.items[this.currentItem].to.uuid;
        const response = await this.mergeItems(fromUuids, toUuid);

        if (response.data.merge) {
          this.skip();
        }
      } catch (error) {
        this.errorMessage = error;
      }
    },
    skip() {
      this.errorMessage = null;
      if (this.currentItem === this.items.length - 1) {
        this.isOpen = false;
        this.currentItem = 0;
        this.$emit("updateTable");
      } else {
        this.currentItem += 1;
      }
    }
  }
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";
</style>
