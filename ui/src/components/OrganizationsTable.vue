<template>
  <v-container>
    <v-row class="actions">
      <h4 class="title">
        <v-icon color="black" left>
          mdi-sitemap
        </v-icon>
        Organizations
      </h4>
      <search
        class="ma-0 ml-auto mr-3 pa-0 flex-grow-0"
        @search="filterSearch"
      />
      <v-btn
        depressed
        color="secondary"
        class="black--text"
        @click.stop="openModal"
      >
        Add
      </v-btn>
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
        />
      </template>
      <template v-slot:expanded-item="{ item }">
        <expanded-organization :domains="item.domains" />
      </template>
    </v-data-table>

    <div class="text-center pt-2">
      <v-pagination
        v-model="page"
        :length="pageCount"
        :total-visible="5"
        @input="getOrganizations($event)"
      ></v-pagination>
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
        <v-card-text>{{ dialog.text }}</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog.open = false">
            Cancel
          </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.open">
      {{ snackbar.text }}
    </v-snackbar>

    <v-card class="dragged-organization" color="primary" dark>
      <v-card-title>
        {{ selectedOrganization }}
      </v-card-title>
      <v-card-subtitle>
        Drag and drop on an individual to affiliate
      </v-card-subtitle>
    </v-card>
  </v-container>
</template>

<script>
import { formatIndividuals } from "../utils/actions";
import ExpandedOrganization from "./ExpandedOrganization.vue";
import OrganizationEntry from "./OrganizationEntry.vue";
import OrganizationModal from "./OrganizationModal.vue";
import Search from "./Search.vue";

export default {
  name: "OrganizationsTable",
  components: {
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
    itemsPerPage: {
      type: Number,
      required: false,
      default: 10
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
        action: ""
      },
      snackbar: {
        open: false,
        text: ""
      },
      modal: {
        open: false,
        organization: undefined,
        domains: []
      },
      selectedOrganization: "",
      filters: {}
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
      }
    },
    confirmEnroll(event) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate the selected items?`,
        text: `Individuals will be enrolled in ${event.organization}`,
        action: () => this.enrollIndividuals(event.uuids, event.organization)
      });
    },
    async enrollIndividuals(uuids, organization) {
      this.dialog.open = false;
      try {
        const response = await Promise.all(
          uuids.map(individual => this.enroll(individual, organization))
        );
        if (response) {
          this.getOrganizations(this.page);
          response.forEach(res => {
            this.$emit("updateWorkspace", {
              update: formatIndividuals([res.data.enroll.individual])
            });
          });
          this.$emit("updateIndividuals");
        }
      } catch (error) {
        Object.assign(this.snackbar, { open: true, text: error });
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
      this.dialog.open = false;
      try {
        const response = await this.deleteOrganization(organization);
        if (response) {
          this.getOrganizations(this.page);
          this.$emit("updateIndividuals");
        }
      } catch (error) {
        Object.assign(this.snackbar, { open: true, text: error });
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
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.actions {
  align-items: baseline;
  justify-content: space-between;
  padding: 0 26px 24px 26px;

  .search {
    width: 200px;
    &:hover {
      width: 200px;
    }
    &--hidden {
      width: 33px;
    }
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
</style>
