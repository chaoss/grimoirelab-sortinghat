<template>
  <v-container>
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
          v-on:dblclick.native="expand(!isExpanded)"
          @expand="expand(!isExpanded)"
          @enroll="confirmEnroll"
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

    <v-dialog v-model="dialog.open" max-width="400">
      <v-card>
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>{{ dialog.text }}</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog.open = false">
            Cancel
          </v-btn>
          <v-btn color="blue darken-4" text @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.open">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script>
import { formatIndividuals } from "../utils/actions";
import ExpandedOrganization from "./ExpandedOrganization.vue";
import OrganizationEntry from "./OrganizationEntry.vue";

export default {
  name: "OrganizationsTable",
  components: { OrganizationEntry, ExpandedOrganization },
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
      }
    };
  },
  created() {
    this.getOrganizations(1);
  },
  methods: {
    async getOrganizations(page) {
      let response = await this.fetchPage(page, this.itemsPerPage);
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
    }
  }
};
</script>
<style scoped>
::v-deep .theme--light.v-pagination .v-pagination__item,
::v-deep .theme--light.v-pagination .v-pagination__navigation {
  box-shadow: none;
}
::v-deep button.v-pagination__item {
  transition: none;
}
</style>
