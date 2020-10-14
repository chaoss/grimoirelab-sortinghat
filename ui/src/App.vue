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
      <v-row>
        <v-col class="individuals elevation-2">
          <individuals-table
            :fetch-page="getIndividualsPage"
            :delete-item="deleteItem"
            @saveIndividual="addSavedIndividual"
          />
        </v-col>
        <v-col class="organizations elevation-2">
          <h4 class="title">Organizations</h4>
          <organizations-table :fetch-page="getOrganizationsPage" />
        </v-col>
      </v-row>
      <v-snackbar v-model="snackbar">
        Individual already in work space
      </v-snackbar>
    </v-content>
  </v-app>
</template>

<script>
import {
  getPaginatedIndividuals,
  getPaginatedOrganizations
} from "./apollo/queries";
import { deleteIdentity } from "./apollo/mutations";
import IndividualsTable from "./components/IndividualsTable";
import OrganizationsTable from "./components/OrganizationsTable";
import WorkSpace from "./components/WorkSpace";

export default {
  name: "App",
  components: {
    IndividualsTable,
    OrganizationsTable,
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
    async getOrganizationsPage(page, items) {
      const response = await getPaginatedOrganizations(
        this.$apollo,
        page,
        items
      );
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
    },
    async deleteItem(uuid) {
      const response = await deleteIdentity(this.$apollo, uuid);
      return response;
    }
  }
};
</script>
<style scoped>
.row {
  justify-content: space-between;
  margin: 32px;
}
.individuals {
  max-width: 1200px;
  width: 70%;
}
.organizations {
  width: 25%;
  max-width: 500px;
  align-self: flex-start;
  margin-left: 32px;
}
h4 {
  padding: 12px 26px;
}
</style>
