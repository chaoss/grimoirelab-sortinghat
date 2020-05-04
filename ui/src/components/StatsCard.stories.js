/* eslint-disable import/no-extraneous-dependencies */
import { storiesOf } from "@storybook/vue";

import StatsCard from "./StatsCard.vue";

export default {
  title: "StatsCard",
  // Our exports that end in "Data" are not stories.
  excludeStories: /.*Data$/
};

export const statsCardData = {
  title: "1.200",
  subTitle: "assigned credits"
};

const statsCardTemplate =
  "<v-container grid-list-xl fluid><v-layout row wrap><v-flex xs4><stats-card :title='title' :subTitle='subTitle' :color='color' :icon='icon'/></v-flex></v-layout></v-container>";

// default color stats card
export const Default = () => ({
  components: { StatsCard },
  template: statsCardTemplate,
  props: {
    title: {
      default: statsCardData.title
    },
    subTitle: {
      default: statsCardData.subTitle
    }
  }
});
// green color stats card
export const Green = () => ({
  components: { StatsCard },
  template: statsCardTemplate,
  props: {
    title: {
      default: statsCardData.title
    },
    subTitle: {
      default: statsCardData.subTitle
    },
    icon: {
      default: "mdi-plus"
    },
    color: {
      default: "green"
    }
  }
});
