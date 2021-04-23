<template>
  <v-main>
    <work-space
      class="ma-md-8 mt-md-6"
      :enroll="enroll"
      :highlight-individual="highlightInWorkspace"
      :individuals="savedIndividuals"
      :merge-items="mergeItems"
      :move-item="moveItem"
      @clearSpace="clearWorkspace"
      @updateIndividuals="updateTable"
      @highlight="highlightIndividual($event, 'highlightInTable', true)"
      @stopHighlight="highlightIndividual($event, 'highlightInTable', false)"
      @deselect="deselectIndividuals"
      @updateOrganizations="updateOrganizations"
      @updateWorkspace="updateWorkspace"
      @updateStore="saveWorkspace($event)"
    />
    <v-row>
      <individuals-table
        class="individuals"
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
        :set-filters="filters"
        :unlock-individual="unlockIndividual"
        :withdraw="withdraw"
        :update-enrollment="updateEnrollment"
        @saveIndividual="addSavedIndividual"
        @updateOrganizations="updateOrganizations"
        @updateWorkspace="updateWorkspace"
        @highlight="highlightIndividual($event, 'highlightInWorkspace', true)"
        @stopHighlight="
          highlightIndividual($event, 'highlightInWorkspace', false)
        "
        ref="table"
      />
      <organizations-table
        class="organizations"
        :fetch-page="getOrganizationsPage"
        :enroll="enroll"
        :add-organization="addOrganization"
        :add-domain="addDomain"
        :delete-domain="deleteDomain"
        :delete-organization="deleteOrganization"
        @getEnrollments="getEnrollments"
        @updateIndividuals="updateTable"
        @updateWorkspace="updateWorkspace"
        ref="organizations"
      />
    </v-row>
    <v-snackbar v-model="snackbar">
      Individual already in work space
    </v-snackbar>
  </v-main>
</template>

<script>
import {
  getCountries,
  getIndividualByUuid,
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
  deleteOrganization,
  addDomain,
  deleteDomain,
  updateProfile,
  lockIndividual,
  unlockIndividual,
  withdraw,
  updateEnrollment
} from "../apollo/mutations";
import IndividualsTable from "../components/IndividualsTable";
import OrganizationsTable from "../components/OrganizationsTable";
import WorkSpace from "../components/WorkSpace";
import { mapActions, mapGetters } from "vuex";
import { formatIndividuals } from "../utils/actions";

export default {
  name: "Dashboard",
  components: {
    IndividualsTable,
    OrganizationsTable,
    WorkSpace
  },
  data() {
    return {
      filters: null,
      highlightInTable: undefined,
      highlightInWorkspace: undefined,
      savedIndividuals: [],
      snackbar: false
    };
  },
  computed: {
    ...mapGetters(["workspace"])
  },
  methods: {
    ...mapActions(["saveWorkspace", "emptyWorkspace"]),
    async getIndividualsPage(page, items, filters, orderBy) {
      const response = await getPaginatedIndividuals(
        this.$apollo,
        page,
        items,
        filters,
        orderBy
      );
      return response;
    },
    async getOrganizationsPage(page, items, filters) {
      const response = await getPaginatedOrganizations(
        this.$apollo,
        page,
        items,
        filters
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
    updateOrganizations() {
      this.$refs.organizations.getOrganizations();
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
    async deleteOrganization(organization) {
      const response = await deleteOrganization(this.$apollo, organization);
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
    },
    async updateEnrollment(data) {
      const response = await updateEnrollment(this.$apollo, data);
      return response;
    },
    clearWorkspace() {
      this.emptyWorkspace();
      this.savedIndividuals = [];
    },
    getEnrollments(organization) {
      this.filters = `enrollment:"${organization}"`;
    }
  },
  async mounted() {
    if (this.workspace && this.workspace.length > 0) {
      const response = await Promise.all(
        this.workspace.map(uuid => getIndividualByUuid(this.$apollo, uuid))
      );
      const individuals = response.map(res => res.data.individuals.entities[0]);
      this.savedIndividuals = formatIndividuals(individuals);
    }
  }
};
</script>
<style lang="scss" scoped>
.row {
  justify-content: space-between;
  margin: 32px;
}
.individuals {
  width: 60%;
  flex-grow: 1;

  .container {
    max-width: 100%;
  }
}
.organizations {
  max-width: 30%;
  min-width: 450px;
  align-self: flex-start;
  margin-left: 32px;

  @media (max-width: 960px) {
    max-width: 100%;
    margin: 32px 0 0 0;
  }
}
h4 {
  padding: 12px 26px;
}
</style>
