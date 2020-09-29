<template>
  <v-card max-width="750">
    <v-container fluid v-if="!noIndividuals">
      <v-row dense>
        <v-col v-for="individual in individuals" :key="individual.profile.id">
          <individual-card
            :name="individual.profile.name"
            :sources="getSources(individual.identities)"
            :is-locked="individual.isLocked"
            :uuid="individual.identities[0].uuid"
            :class="{ selected: isSelected(individual.identities[0].uuid) }"
            @click="selectIndividual(individual.identities[0].uuid)"
          />
        </v-col>
      </v-row>
    </v-container>
    <v-card-text v-else>No individuals found</v-card-text>
  </v-card>
</template>

<script>
import IndividualCard from "./IndividualCard.vue";
import { mapState } from "vuex";
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
    ...mapState(["selectedIndividual", "selectedIndividuals"]),
    noIndividuals: function() {
      return this.individuals.length === 0;
    }
  },
  methods: {
    getSources(identities) {
      const icons = ["git", "github", "gitlab"];
      const sources = identities.map(identity => {
        if (icons.find(icon => icon === identity.source.toLowerCase())) {
          return identity.source;
        } else {
          return "Others";
        }
      });

      return [...new Set(sources)];
    },
    selectIndividual(uuid) {
      if (this.$store) {
        this.$store.commit("addIndividual", uuid);
      }
    },
    isSelected(uuid) {
      if (this.$store) {
        return this.selectedIndividuals.find(individual => individual === uuid);
      } else {
        return false;
      }
    }
  }
};
</script>
