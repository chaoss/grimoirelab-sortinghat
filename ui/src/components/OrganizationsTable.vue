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
  </v-container>
</template>

<script>
import ExpandedOrganization from "./ExpandedOrganization.vue";
import OrganizationEntry from "./OrganizationEntry.vue";

export default {
  name: "OrganizationsTable",
  components: { OrganizationEntry, ExpandedOrganization },
  props: {
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
      page: 0
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
