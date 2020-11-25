<template>
  <v-content>
    <work-space
      :highlight-individual="highlightInWorkspace"
      :individuals="savedIndividuals"
      :merge-items="mergeItems"
      :move-item="moveItem"
      @clearSpace="savedIndividuals = []"
      @updateIndividuals="updateTable"
      @highlight="highlightIndividual($event, 'highlightInTable', true)"
      @stopHighlight="highlightIndividual($event, 'highlightInTable', false)"
      @deselect="deselectIndividuals"
    />
    <v-row>
      <v-col class="individuals elevation-2">
        <individuals-table
          :fetch-page="getIndividualsPage"
          :delete-item="deleteItem"
          :merge-items="mergeItems"
          :unmerge-items="unmergeItems"
          :move-item="moveItem"
          :highlight-individual="highlightInTable"
          :add-identity="addIdentity"
          :updateProfile="updateProfile"
          :enroll="enroll"
          :get-countries="getCountries"
          :lock-individual="lockIndividual"
          :unlock-individual="unlockIndividual"
          :withdraw="withdraw"
          @saveIndividual="addSavedIndividual"
          @updateWorkspace="updateWorkspace"
          @highlight="highlightIndividual($event, 'highlightInWorkspace', true)"
          @stopHighlight="
            highlightIndividual($event, 'highlightInWorkspace', false)
          "
          ref="table"
        />
      </v-col>
      <v-col class="organizations elevation-2">
        <organizations-table
          :fetch-page="getOrganizationsPage"
          :enroll="enroll"
          :add-organization="addOrganization"
          :add-domain="addDomain"
          :delete-domain="deleteDomain"
          @updateIndividuals="updateTable"
          @updateWorkspace="updateWorkspace"
        />
      </v-col>
    </v-row>
    <v-snackbar v-model="snackbar">
      Individual already in work space
    </v-snackbar>
  </v-content>
</template>

<script>
import {
  getCountries,
  getPaginatedIndividuals,
  getPaginatedOrganizations
} from "../apollo/queries";
import {
  addIdentity,
  deleteIdentity,
  merge,
  unmerge,
  moveIdentity,
  enroll,
  addOrganization,
  addDomain,
  deleteDomain,
  updateProfile,
  lockIndividual,
  unlockIndividual,
  withdraw
} from "../apollo/mutations";
import IndividualsTable from "../components/IndividualsTable";
import OrganizationsTable from "../components/OrganizationsTable";
import WorkSpace from "../components/WorkSpace";

export default {
  name: "Dashboard",
  components: {
    IndividualsTable,
    OrganizationsTable,
    WorkSpace
  },
  data() {
    return {
      highlightInTable: undefined,
      highlightInWorkspace: undefined,
      savedIndividuals: [],
      snackbar: false
    };
  },
  methods: {
    async getIndividualsPage(page, items, filters) {
      const response = await getPaginatedIndividuals(
        this.$apollo,
        page,
        items,
        filters
      );
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
    },
    async mergeItems(fromUuids, toUuid) {
      const response = await merge(this.$apollo, fromUuids, toUuid);
      return response;
    },
    updateTable() {
      this.$refs.table.queryIndividuals();
    },
    updateWorkspace(event) {
      if (event.remove) {
        event.remove.forEach(removedItem => {
          const removedIndex = this.savedIndividuals.findIndex(
            individual => individual.uuid == removedItem
          );
          if (removedIndex !== -1) {
            this.savedIndividuals.splice(removedIndex, 1);
          }
        });
      }
      if (event.update) {
        event.update.forEach(updatedItem => {
          const updatedIndex = this.savedIndividuals.findIndex(
            individual => individual.uuid == updatedItem.uuid
          );
          if (updatedIndex !== -1) {
            Object.assign(this.savedIndividuals[updatedIndex], updatedItem);
          }
        });
      }
    },
    highlightIndividual(individual, component, highlight) {
      this[component] = highlight ? individual.uuid : undefined;
    },
    async unmergeItems(uuids) {
      const response = await unmerge(this.$apollo, uuids);
      return response;
    },
    async moveItem(fromUuid, toUuid) {
      const response = await moveIdentity(this.$apollo, fromUuid, toUuid);
      return response;
    },
    deselectIndividuals() {
      this.$refs.table.deselectIndividuals();
    },
    async enroll(uuid, organization, fromDate, toDate) {
      const response = await enroll(
        this.$apollo,
        uuid,
        organization,
        fromDate,
        toDate
      );
      return response;
    },
    async addIdentity(email, name, source, username) {
      const response = await addIdentity(
        this.$apollo,
        email,
        name,
        source,
        username
      );
      return response;
    },
    async updateProfile(data, uuid) {
      const response = updateProfile(this.$apollo, data, uuid);
      return response;
    },
    async addOrganization(organization) {
      const response = await addOrganization(this.$apollo, organization);
      return response;
    },
    async addDomain(domain, organization) {
      const response = await addDomain(this.$apollo, domain, organization);
      return response;
    },
    async deleteDomain(domain) {
      const response = await deleteDomain(this.$apollo, domain);
      return response;
    },
    async getCountries() {
      const response = await getCountries(this.$apollo);
      return response.data.countries.entities;
    },
    async lockIndividual(uuid) {
      const response = await lockIndividual(this.$apollo, uuid);
      return response;
    },
    async unlockIndividual(uuid) {
      const response = await unlockIndividual(this.$apollo, uuid);
      return response;
    },
    async withdraw(uuid, organization, fromDate, toDate) {
      const response = await withdraw(
        this.$apollo,
        uuid,
        organization,
        fromDate,
        toDate
      );
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
