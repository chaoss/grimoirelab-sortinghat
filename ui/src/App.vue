<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <div class="d-flex align-center">
        <v-img
          alt="Vuetify Logo"
          class="shrink mr-2"
          contain
          src="https://cdn.vuetifyjs.com/images/logos/vuetify-logo-dark.png"
          transition="scale-transition"
          width="40"
        />

        <v-img
          alt="Vuetify Name"
          class="shrink mt-1 hidden-sm-and-down"
          contain
          min-width="100"
          src="https://cdn.vuetifyjs.com/images/logos/vuetify-name-dark.png"
          width="100"
        />
      </div>

      <v-spacer></v-spacer>

      <v-btn
        href="https://github.com/vuetifyjs/vuetify/releases/latest"
        target="_blank"
        text
      >
        <span class="mr-2">Latest Release</span>
        <v-icon>mdi-open-in-new</v-icon>
      </v-btn>
    </v-app-bar>

    <v-content>
      <work-space
        :individuals="savedIndividuals"
        @clearSpace="savedIndividuals = []"
      />
      <v-container max-width="900">
        <individuals-table
          :fetch-page="getIndividualsPage"
          @saveIndividual="addSavedIndividual"
        />
      </v-container>
      <v-snackbar v-model="snackbar">
        Individual already in work space
      </v-snackbar>
    </v-content>
  </v-app>
</template>

<script>
import { getPaginatedIndividuals } from "./apollo/queries";
import IndividualsTable from "./components/IndividualsTable";
import WorkSpace from "./components/WorkSpace";

export default {
  name: "App",
  components: {
    IndividualsTable,
    WorkSpace
  },
  data() {
    return {
      savedIndividuals: [],
      snackbar: false
    };
  },
  methods: {
    async getIndividualsPage(page, items) {
      const response = await getPaginatedIndividuals(this.$apollo, page, items);
      return response;
    },
    addSavedIndividual(individual) {
      const isSaved = this.savedIndividuals.find(savedIndividual => {
        return individual.uuid === savedIndividual.uuid;
      });
      if (isSaved) {
        this.snackbar = true;
        return;
      }
      this.savedIndividuals.push(individual);
    }
  }
};
</script>
