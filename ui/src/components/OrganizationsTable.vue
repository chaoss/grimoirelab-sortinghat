<template>
  <section class="section">
    <v-row class="header">
      <h4 class="title">
        <v-icon color="black" size="small" start>
          {{ isGroup ? "mdi-account-group" : "mdi-sitemap" }}
        </v-icon>
        {{ name }}
        <v-chip pill density="comfortable" class="ml-2">{{
          totalResults
        }}</v-chip>
      </h4>
      <v-btn
        color="secondary"
        class="black--text"
        size="small"
        variant="flat"
        height="34"
        @click.stop="openModal"
      >
        Add
      </v-btn>
    </v-row>

    <v-row class="actions">
      <search
        class="pa-0 flex-grow-1"
        :valid-filters="[]"
        @search="filterSearch"
      />
    </v-row>

    <v-data-table-server
      :headers="headers"
      :items="items"
      :items-length="totalResults"
      :items-per-page="itemsPerPage"
      :expanded="expandedItems"
      item-key="id"
      item-value="name"
      v-model:page="page"
      :loading="loading"
      hover
      return-object
      @update:expanded="($event) => (expandedItems = $event)"
    >
      <template v-slot:item="{ item, internalItem, toggleExpand, isExpanded }">
        <organization-entry
          :name="item.name"
          :enrollments="getEnrolledIndividuals(item.enrollments)"
          :is-expanded="isExpanded(internalItem)"
          :is-editable="!isGroup"
          draggable="true"
          @dblclick="expand(!isExpanded)"
          @dragstart="startDrag(item, $event)"
          @expand="toggleExpand(internalItem)"
          @enroll="confirmEnroll"
          @edit="openModal(item)"
          @delete="confirmDelete(item.name)"
          @getEnrollments="$emit('getEnrollments', { enrollment: item.name })"
          @addTeam="createTeam(item.name, $event)"
          @merge:orgs="confirmMerge"
        />
      </template>
      <template v-slot:expanded-row="{ item }">
        <expanded-organization
          :organization="item.name"
          :is-group="isGroup"
          :domains="item.domains"
          :add-team="addTeam"
          :delete-team="deleteTeam"
          :fetch-teams="fetchTeams"
          @enroll="confirmEnroll"
          @getEnrollments="$emit('getEnrollments', $event)"
          :ref="item.id"
        />
      </template>
      <template v-slot:bottom>
        <div class="pagination text-center pa-3">
          <div aria-hidden="true" />
          <v-pagination
            v-model="page"
            :length="pageCount"
            :total-visible="5"
            density="compact"
            @update:modelValue="getTableItems($event)"
          ></v-pagination>
          <v-text-field
            :model-value="itemsPerPage"
            class="mr-3"
            density="compact"
            label="Items per page"
            type="number"
            min="1"
            hide-details
            :max="totalResults"
            @update:modelValue="changeItemsPerPage($event)"
          ></v-text-field>
        </div>
      </template>
      <template v-slot:no-data>
        <v-alert v-if="error" class="text-left" density="compact" type="error">
          {{ error }}
        </v-alert>
        <p v-else-if="Object.keys(filters).length > 0">
          No results matched your search.
        </p>
        <p v-else>No data available</p>
      </template>
    </v-data-table-server>

    <organization-modal
      v-if="!isGroup"
      v-model:is-open="modal.open"
      :add-organization="addOrganization"
      :add-domain="addDomain"
      :delete-domain="deleteDomain"
      :organization="modal.organization"
      :domains="modal.domains"
      :aliases="modal.aliases"
      :add-alias="addAlias"
      :delete-alias="deleteAlias"
      @updateOrganizations="getTableItems(page)"
    />

    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p class="pt-2 pb-2 text-body-2">{{ dialog.text }}</p>
          <div v-if="dialog.showDates">
            <h6 class="subheader">Enrollment dates (optional)</h6>
            <v-row>
              <v-col cols="6">
                <date-input
                  v-model="dialog.dateFrom"
                  label="Date from"
                  outlined
                />
              </v-col>
              <v-col cols="6">
                <date-input v-model="dialog.dateTo" label="Date to" outlined />
              </v-col>
            </v-row>
          </div>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog"> Cancel </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog"> OK </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </section>
</template>

<script>
import { formatIndividuals } from "../utils/actions";
import DateInput from "./DateInput.vue";
import ExpandedOrganization from "./ExpandedOrganization.vue";
import OrganizationEntry from "./OrganizationEntry.vue";
import OrganizationModal from "./OrganizationModal.vue";
import Search from "./Search.vue";

export default {
  name: "OrganizationsTable",
  components: {
    DateInput,
    OrganizationEntry,
    ExpandedOrganization,
    OrganizationModal,
    Search,
  },
  props: {
    name: {
      type: String,
      required: false,
      default: "Organizations",
    },
    isGroup: {
      type: Boolean,
      required: false,
      default: false,
    },
    enroll: {
      type: Function,
      required: true,
    },
    fetchPage: {
      type: Function,
      required: true,
    },
    fetchTeams: {
      type: Function,
      required: true,
    },
    addOrganization: {
      type: Function,
      required: true,
    },
    deleteOrganization: {
      type: Function,
      required: true,
    },
    addTeam: {
      type: Function,
      required: true,
    },
    deleteTeam: {
      type: Function,
      required: true,
    },
    addDomain: {
      type: Function,
      required: false,
    },
    deleteDomain: {
      type: Function,
      required: false,
    },
    mergeItems: {
      type: Function,
      required: false,
    },
    addAlias: {
      type: Function,
      required: false,
    },
    deleteAlias: {
      type: Function,
      required: false,
    },
  },
  data() {
    return {
      headers: [
        { value: "name", title: "Name", sortable: false },
        {
          value: "enrollments",
          title: "Enrollments",
          align: "end",
          sortable: false,
        },
        { value: "actions", sortable: false },
      ],
      expandedItems: [],
      items: [],
      pageCount: 0,
      page: 0,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: "",
        showDates: false,
        dateFrom: null,
        dateTo: null,
      },
      modal: {
        open: false,
        organization: undefined,
        domains: [],
        aliases: [],
      },
      selectedOrganization: "",
      filters: {},
      totalResults: 0,
      itemsPerPage: 10,
      forms: {
        teamName: "",
      },
      loading: false,
      error: null,
    };
  },
  created() {
    this.getTableItems(1);
  },
  methods: {
    async getTableItems(page = this.page, filters = this.filters) {
      this.loading = true;
      this.error = null;
      try {
        let response = await this.fetchPage(page, this.itemsPerPage, filters);
        if (response) {
          this.items = response.entities;
          this.pageCount = response.pageInfo.numPages;
          this.page = response.pageInfo.page;
          this.totalResults = response.pageInfo.totalResults;
        }
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    confirmEnroll(event) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate the selected individuals?`,
        text: `Individuals will be enrolled in ${event.group}`,
        showDates: true,
        action: () =>
          this.enrollIndividuals(
            event.individuals,
            event.group,
            this.dialog.dateFrom,
            this.dialog.dateTo,
            event.parentOrg
          ),
      });
    },
    async enrollIndividuals(individuals, group, dateFrom, dateTo, parentOrg) {
      this.closeDialog();
      try {
        const response = await Promise.all(
          individuals.map((individual) =>
            this.enroll(individual.uuid, group, dateFrom, dateTo, parentOrg)
          )
        );
        response.forEach((res) => {
          this.$emit("updateWorkspace", {
            update: formatIndividuals([res.data.enroll.individual]),
          });
        });
        this.$logger.debug("Enrolled individuals", {
          group,
          individuals,
          dateFrom,
          dateTo,
          parentOrg,
        });

        if (parentOrg) {
          const notInOrg = individuals.filter(
            (individual) =>
              !individual.enrollments.some(
                (enrollment) => enrollment.group.name === parentOrg
              )
          );
          if (notInOrg.length > 0) {
            const responses = await Promise.all(
              notInOrg.map((individual) =>
                this.enroll(individual.uuid, parentOrg, dateFrom, dateTo)
              )
            );
            responses.forEach((res) => {
              this.$emit("updateWorkspace", {
                update: formatIndividuals([res.data.enroll.individual]),
              });
            });
            this.$logger.debug("Enrolled individuals", {
              group: parentOrg,
              uuids: notInOrg,
              dateFrom,
              dateTo,
            });
          }
          const updatedItem = this.expandedItems.find(
            (item) => item.name === parentOrg
          );
          this.$refs[updatedItem.id].reloadTeams();
        }
        this.getTableItems(this.page);
        this.$emit("updateIndividuals");
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error enrolling individuals: ${error}`, {
          group,
          individuals,
          dateFrom,
          dateTo,
          parentOrg,
        });
      }
    },
    openModal(organization) {
      const domains =
        organization.domains && organization.domains.length > 0
          ? organization.domains.map((domain) => domain)
          : [{ domain: "", isTopDomain: false }];
      const aliases = organization.aliases?.map((item) => item.alias) || [""];
      Object.assign(this.modal, {
        open: true,
        organization: organization ? organization.name : "",
        domains: domains,
        aliases: aliases,
      });
    },
    confirmDelete(group) {
      Object.assign(this.dialog, {
        open: true,
        title: `Delete ${group}?`,
        text: "",
        action: () => this.deleteGroup(group),
      });
    },
    async deleteGroup(item) {
      this.closeDialog();
      try {
        const response = await this.deleteOrganization(item);
        if (response) {
          this.getTableItems(this.page);
          this.$emit("updateIndividuals");
          this.$logger.debug(`Deleted ${item}`);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error deleting ${item}: ${error}`);
      }
    },
    startDrag(item, event) {
      this.selectedOrganization = item.name;
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.setData("type", "enrollFromOrganization");
      event.dataTransfer.setData("group", item.name);
    },
    filterSearch(filters) {
      this.filters = filters;
      this.getTableItems(1);
    },
    changeItemsPerPage(value) {
      if (value) {
        this.itemsPerPage = parseInt(value, 10);
        this.getTableItems(1);
      }
    },
    closeDialog() {
      Object.assign(this.dialog, {
        open: false,
        title: "",
        text: "",
        action: "",
        showDates: false,
        dateFrom: null,
        dateTo: null,
      });
    },
    async addUnaffiliatedTeam() {
      try {
        const response = await this.addTeam(this.forms.teamName);
        if (response) {
          this.getTableItems();
          this.$logger.debug(`Added team ${this.forms.teamName}`);
          this.forms.teamName = "";
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(
          `Error adding team ${this.forms.teamName}: ${error}`
        );
      }
    },
    getEnrolledIndividuals(enrollments) {
      if (!enrollments) {
        return 0;
      }
      const uniqueIndividuals = new Set(enrollments.map((item) => item.id));

      return uniqueIndividuals.size;
    },
    async createTeam(organization, team) {
      try {
        const response = await this.addTeam(team, organization);
        if (!response.errors) {
          const updatedItem = this.expandedItems.find(
            (item) => item.name === organization
          );
          if (updatedItem) {
            this.$refs[updatedItem.id].reloadTeams();
          }
        }
      } catch (error) {
        Object.assign(this.dialog, {
          isOpen: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error creating team: ${error}`);
      }
    },
    confirmMerge({ fromOrg, toOrg }) {
      Object.assign(this.dialog, {
        open: true,
        title: `Merge ${fromOrg} with ${toOrg}?`,
        text: `${fromOrg} will be deleted.`,
        action: () => this.merge(fromOrg, toOrg),
      });
    },
    async merge(fromOrg, toOrg) {
      try {
        const response = await this.mergeItems(fromOrg, toOrg);
        if (!response.errors) {
          this.getTableItems();
          this.closeDialog();
          this.$logger.debug(`Merged organization ${fromOrg} with ${toOrg}`);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error merging ${fromOrg} with ${toOrg}: ${error}`);
      }
    },
  },
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.actions {
  align-items: baseline;
  justify-content: space-between;
  padding: 0 26px 15px 26px;
  .search {
    width: 60%;
  }
  .title {
    @media (max-width: 1818px) {
      flex-basis: 100%;
      margin-bottom: 8px;
    }
  }
}

.dragged-organization {
  max-width: 400px;
  position: absolute;
  top: -400px;
}

.pagination {
  display: grid;
  grid-template-columns: minmax(0px, 5.8rem) auto minmax(5.8rem, 17%);
}

:deep(.v-data-table__th:first-of-type) {
  padding-left: 30px;
}
</style>
