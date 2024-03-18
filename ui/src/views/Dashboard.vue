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
      <v-col lg="8" sm="12" class="pt-0 pl-0 pr-sm-0 pr-lg-4">
        <individuals-table
          class="individuals"
          is-expandable
          outlined
          :fetch-page="getIndividualsPage"
          :delete-item="deleteItem"
          :merge-items="mergeItems"
          :unmerge-items="unmergeItems"
          :move-item="moveItem"
          :highlight-individual="highlightInTable"
          :add-identity="addIdentity"
          :updateProfile="updateProfile"
          :enroll="enroll"
          :fetch-organizations="getOrganizationsPage"
          :get-countries="getCountries"
          :lock-individual="lockIndividual"
          :set-filters="filters"
          :unlock-individual="unlockIndividual"
          :withdraw="withdraw"
          :update-enrollment="updateEnrollment"
          :recommend-matches="recommendMatches"
          @saveIndividuals="addSavedIndividuals"
          @setFilters="filters = $event"
          @updateOrganizations="updateOrganizations"
          @updateWorkspace="updateWorkspace"
          @highlight="highlightIndividual($event, 'highlightInWorkspace', true)"
          @stopHighlight="
            highlightIndividual($event, 'highlightInWorkspace', false)
          "
          ref="table"
        />
      </v-col>
      <v-col
        lg="4"
        sm="12"
        class="organizations mt-4 mt-lg-0 pt-0 pl-sm-0 pl-lg-4 pr-0"
      >
        <organizations-table
          :fetch-page="getOrganizationsPage"
          :enroll="enroll"
          :add-organization="addOrganization"
          :add-domain="addDomain"
          :delete-domain="deleteDomain"
          :delete-organization="deleteOrganization"
          :add-team="addTeam"
          :delete-team="deleteTeam"
          :fetch-teams="fetchTeams"
          :merge-items="mergeOrgs"
          :add-alias="addAlias"
          :delete-alias="deleteAlias"
          @getEnrollments="getEnrollments"
          @updateIndividuals="updateTable"
          @updateWorkspace="updateWorkspace"
          ref="organizations"
        />
      </v-col>
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
  getPaginatedOrganizations,
  getTeams,
  getPaginatedMergeRecommendations,
  getRecommendedMergesCount,
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
  addTeam,
  deleteTeam,
  updateProfile,
  lockIndividual,
  unlockIndividual,
  withdraw,
  updateEnrollment,
  manageMergeRecommendation,
  recommendMatches,
  mergeOrganizations,
  addAlias,
  deleteAlias,
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
    WorkSpace,
  },
  data() {
    return {
      filters: null,
      highlightInTable: undefined,
      highlightInWorkspace: undefined,
      savedIndividuals: [],
      snackbar: false,
    };
  },
  computed: {
    ...mapGetters(["workspace"]),
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
      return response.data.organizations;
    },
    async fetchTeams(filters) {
      const response = await getTeams(this.$apollo, filters);
      return response;
    },
    addSavedIndividuals(individuals, overwriteIndividuals) {
      individuals.forEach((individual) => {
        const isSaved = this.savedIndividuals.find((savedIndividual) => {
          return individual.uuid === savedIndividual.uuid;
        });
        if (isSaved) {
          if (overwriteIndividuals) {
            const index = this.savedIndividuals.findIndex((savedIndividual) => {
              return individual.uuid === savedIndividual.uuid;
            });
            Object.assign(this.savedIndividuals[index], individual);
          } else {
            this.snackbar = true;
          }
          return;
        }
        this.savedIndividuals.push(individual);
      });
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
      this.$refs.organizations.getTableItems();

      const openOrgs = this.$refs.organizations.$refs;
      Object.keys(openOrgs).forEach((key) => openOrgs[key]?.reloadTeams());
    },
    updateTable() {
      this.$refs.table.queryIndividuals();
    },
    updateWorkspace(event) {
      if (event.remove) {
        event.remove.forEach((removedItem) => {
          const removedIndex = this.savedIndividuals.findIndex(
            (individual) => individual.uuid == removedItem
          );
          if (removedIndex !== -1) {
            this.savedIndividuals.splice(removedIndex, 1);
          }
        });
      }
      if (event.update) {
        event.update.forEach((updatedItem) => {
          const updatedIndex = this.savedIndividuals.findIndex(
            (individual) => individual.uuid == updatedItem.uuid
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
    async enroll(uuid, group, fromDate, toDate, parentOrg) {
      const response = await enroll(
        this.$apollo,
        uuid,
        group,
        fromDate,
        toDate,
        parentOrg
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
    async addTeam(team, organization, parent) {
      const response = await addTeam(this.$apollo, team, organization, parent);
      return response;
    },
    async deleteTeam(team, organization) {
      const response = await deleteTeam(this.$apollo, team, organization);
      return response;
    },
    async addDomain(domain, isTopDomain, organization) {
      const response = await addDomain(
        this.$apollo,
        domain,
        isTopDomain,
        organization
      );
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
    async withdraw(uuid, group, fromDate, toDate, parentOrg) {
      const response = await withdraw(
        this.$apollo,
        uuid,
        group,
        fromDate,
        toDate,
        parentOrg
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
    getEnrollments({ enrollment, parentOrg }) {
      let newFilters = `enrollment:"${enrollment}"`;
      if (parentOrg) {
        newFilters = newFilters.concat(` enrollmentParentOrg:"${parentOrg}"`);
      }
      if (this.filters === newFilters) {
        this.$refs.table.queryIndividuals();
      }
      this.$nextTick(() => (this.filters = newFilters));
    },
    async getRecommendations(page, pageSize) {
      const response = await getPaginatedMergeRecommendations(
        this.$apollo,
        page,
        pageSize
      );
      return response;
    },
    async getRecommendationsCount() {
      const response = await getRecommendedMergesCount(this.$apollo);
      return response;
    },
    async manageRecommendation(id, apply) {
      const response = await manageMergeRecommendation(this.$apollo, id, apply);
      return response;
    },
    async recommendMatches(criteria, exclude, uuid) {
      const response = await recommendMatches(
        this.$apollo,
        criteria,
        exclude,
        uuid
      );
      return response;
    },
    async mergeOrgs(fromOrg, toOrg) {
      const response = await mergeOrganizations(this.$apollo, fromOrg, toOrg);
      return response;
    },
    async addAlias(alias, organization) {
      const response = await addAlias(this.$apollo, alias, organization);
      return response;
    },
    async deleteAlias(alias) {
      const response = await deleteAlias(this.$apollo, alias);
      return response;
    },
  },
  async mounted() {
    if (this.workspace && this.workspace.length > 0) {
      const response = await Promise.all(
        this.workspace.map((uuid) => getIndividualByUuid(this.$apollo, uuid))
      );
      const individuals = response.map(
        (res) => res.data.individuals.entities[0]
      );
      this.savedIndividuals = formatIndividuals(individuals);
    }
  },
  provide() {
    return {
      getRecommendations: this.getRecommendations,
      getRecommendationsCount: this.getRecommendationsCount,
      manageRecommendation: this.manageRecommendation,
    };
  },
};
</script>
<style lang="scss" scoped>
.v-row {
  justify-content: space-between;
  margin: 32px;
}
h4 {
  padding: 12px 26px;
}
</style>
