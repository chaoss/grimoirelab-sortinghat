<template>
  <section class="section">
    <v-row class="header">
      <h4 class="title">
        <v-icon color="black" left dense>
          mdi-sitemap
        </v-icon>
        Organizations
        <v-chip pill small class="ml-2">{{ totalResults }}</v-chip>
      </h4>
      <v-btn
        depressed
        small
        height="34"
        color="secondary"
        class="black--text"
        @click.stop="openModal"
      >
        Add
      </v-btn>
    </v-row>

    <v-row class="actions">
      <search
        class="mr-3 pa-0 flex-grow-0"
        :valid-filters="[]"
        @search="filterSearch"
      />
    </v-row>

    <v-data-table
      hide-default-header
      hide-default-footer
      :headers="headers"
      :items="organizations"
      :expanded.sync="expandedItems"
      item-key="id"
      :page.sync="page"
    >
      <template v-slot:item="{ item, expand, isExpanded }">
        <organization-entry
          :name="item.name"
          :enrollments="item.enrollments.length"
          :domains="item.domains"
          :is-expanded="isExpanded"
          draggable
          v-on:dblclick.native="expand(!isExpanded)"
          @dragstart.native="startDrag(item, $event)"
          @expand="expand(!isExpanded)"
          @enroll="confirmEnroll"
          @edit="openModal(item)"
          @delete="confirmDelete(item.name)"
          @getEnrollments="$emit('getEnrollments', item.name)"
        />
      </template>
      <template v-slot:expanded-item="{ item }">
        <expanded-organization :domains="item.domains" />
      </template>
    </v-data-table>

    <div class="pagination d-flex align-baseline text-center pa-2">
      <v-pagination
        v-model="page"
        :length="pageCount"
        :total-visible="5"
        @input="getOrganizations($event)"
      ></v-pagination>
      <v-text-field
        :value="itemsPerPage"
        class="mr-3"
        label="Items per page"
        type="number"
        min="1"
        :max="totalResults"
        @change="changeItemsPerPage($event)"
      ></v-text-field>
    </div>

    <organization-modal
      :is-open.sync="modal.open"
      :add-organization="addOrganization"
      :add-domain="addDomain"
      :delete-domain="deleteDomain"
      :organization="modal.organization"
      :domains="modal.domains"
      @updateOrganizations="getOrganizations(page)"
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
          <v-btn text @click="closeDialog">
            Cancel
          </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-card class="dragged-organization" color="primary" dark>
      <v-card-title>
        {{ selectedOrganization }}
      </v-card-title>
      <v-card-subtitle>
        Drag and drop on an individual to affiliate
      </v-card-subtitle>
    </v-card>
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
    Search
  },
  props: {
    enroll: {
      type: Function,
      required: true
    },
    fetchPage: {
      type: Function,
      required: true
    },
    addOrganization: {
      type: Function,
      required: true
    },
    deleteOrganization: {
      type: Function,
      required: true
    },
    addDomain: {
      type: Function,
      required: true
    },
    deleteDomain: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      headers: [
        { value: "name" },
        { value: "enrollments" },
        { value: "actions" }
      ],
      expandedItems: [],
      organizations: [],
      pageCount: 0,
      page: 0,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: "",
        showDates: false,
        dateFrom: null,
        dateTo: null
      },
      modal: {
        open: false,
        organization: undefined,
        domains: []
      },
      selectedOrganization: "",
      filters: {},
      totalResults: 0,
      itemsPerPage: 10
    };
  },
  created() {
    this.getOrganizations(1);
  },
  methods: {
    async getOrganizations(page = this.page, filters = this.filters) {
      let response = await this.fetchPage(page, this.itemsPerPage, filters);
      if (response) {
        this.organizations = response.data.organizations.entities;
        this.pageCount = response.data.organizations.pageInfo.numPages;
        this.page = response.data.organizations.pageInfo.page;
        this.totalResults = response.data.organizations.pageInfo.totalResults;
      }
    },
    confirmEnroll(event) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate the selected individuals?`,
        text: `Individuals will be enrolled in ${event.organization}`,
        showDates: true,
        action: () =>
          this.enrollIndividuals(
            event.uuids,
            event.organization,
            this.dialog.dateFrom,
            this.dialog.dateTo
          )
      });
    },
    async enrollIndividuals(uuids, organization, dateFrom, dateTo) {
      this.closeDialog();
      try {
        const response = await Promise.all(
          uuids.map(individual =>
            this.enroll(individual, organization, dateFrom, dateTo)
          )
        );
        if (response) {
          this.getOrganizations(this.page);
          response.forEach(res => {
            this.$emit("updateWorkspace", {
              update: formatIndividuals([res.data.enroll.individual])
            });
          });
          this.$emit("updateIndividuals");
          this.$logger.debug("Enrolled individuals", {
            organization,
            uuids,
            dateFrom,
            dateTo
          });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(`Error enrolling individuals: ${error}`, {
          organization,
          uuids,
          dateFrom,
          dateTo
        });
      }
    },
    openModal(organization) {
      const domains =
        organization.domains && organization.domains.length > 0
          ? organization.domains.map(domain => domain.domain)
          : [""];
      Object.assign(this.modal, {
        open: true,
        organization: organization ? organization.name : "",
        domains: domains
      });
    },
    confirmDelete(organization) {
      Object.assign(this.dialog, {
        open: true,
        title: "Delete this organization?",
        text: organization,
        action: () => this.deleteOrg(organization)
      });
    },
    async deleteOrg(organization) {
      this.closeDialog();
      try {
        const response = await this.deleteOrganization(organization);
        if (response) {
          this.getOrganizations(this.page);
          this.$emit("updateIndividuals");
          this.$logger.debug(`Deleted organization ${organization}`);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(
          `Error deleting organization ${organization}: ${error}`
        );
      }
    },
    startDrag(item, event) {
      this.selectedOrganization = item.name;
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.setData("type", "enrollFromOrganization");
      event.dataTransfer.setData("organization", item.name);
      const dragImage = document.querySelector(".dragged-organization");
      event.dataTransfer.setDragImage(dragImage, 0, 0);
    },
    filterSearch(filters) {
      this.filters = filters;
      this.getOrganizations(1);
    },
    changeItemsPerPage(value) {
      if (value) {
        this.itemsPerPage = parseInt(value, 10);
        this.getOrganizations(1);
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
        dateTo: null
      });
    }
  }
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
  nav {
    margin-left: 17%;
    flex-grow: 1;
  }
  .v-input {
    min-width: 17%;
    max-width: 17%;
  }
}
</style>
