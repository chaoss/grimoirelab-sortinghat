<template>
  <v-card class="mx-auto" max-width="750">
    <v-container fluid v-if="!noIndividuals">
      <v-row dense>
        <v-col v-for="individual in individuals" :key="individual">
          <individual-card :name="individual" />
        </v-col>
      </v-row>
    </v-container>
    <v-card-text v-else>No individuals found</v-card-text>
  </v-card>
</template>

<script>
import IndividualCard from "./IndividualCard.vue";
export default {
  name: "individualsgrid",
  components: {
    IndividualCard
  },
  props: {
    individuals: {
      type: Array,
      required: true
    }
  },
  computed: {
    noIndividuals: function() {
      return this.individuals.length === 0;
    }
  }
};
</script>
