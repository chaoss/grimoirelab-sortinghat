<template>
  <v-container>
    <v-data-table
      hide-default-header
      hide-default-footer
      :headers="headers"
      :items="individuals"
      :expanded.sync="expandedItems"
      item-key="id"
      :page.sync="page"
    >
      <template v-slot:item="{ item, expand, isExpanded }">
        <individual-entry
          :name="item.name"
          :organization="item.organization"
          :email="item.email"
          :sources="item.sources"
          :is-expanded="isExpanded"
          :is-locked="item.isLocked"
          :is-bot="item.isBot"
          @expand="expand(!isExpanded)"
        />
      </template>
      <template v-slot:expanded-item="{ item }">
        <expanded-individual
          :enrollments="item.enrollments"
          :identities="item.identities"
        />
      </template>
    </v-data-table>
    <div class="text-center pt-2">
      <v-pagination
        v-model="page"
        :length="pageCount"
        :total-visible="7"
        @input="queryIndividuals($event)"
      ></v-pagination>
    </div>
  </v-container>
</template>

<script>
import IndividualEntry from "./IndividualEntry.vue";
import ExpandedIndividual from "./ExpandedIndividual.vue";

export default {
  name: "IndividualsTable",
  components: {
    IndividualEntry,
    ExpandedIndividual
  },
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
        { value: "email" },
        { value: "sources" },
        { value: "actions" }
      ],
      individuals: [],
      expandedItems: [],
      pageCount: 0,
      page: 0
    };
  },
  created() {
    this.queryIndividuals(1);
  },
  methods: {
    async queryIndividuals(page) {
      let response = await this.fetchPage(page, this.itemsPerPage);
      if (response) {
        this.individuals = this.formatIndividuals(
          response.data.individuals.entities
        );
        this.pageCount = response.data.individuals.pageInfo.numPages;
        this.page = response.data.individuals.pageInfo.page;
      }
    },
    formatIndividuals(individuals) {
      const formattedList = individuals.map(item => {
        return {
          name: item.profile.name,
          id: item.profile.id,
          email: item.profile.email,
          organization: item.enrollments[0]
            ? item.enrollments[0].organization.name
            : "",
          sources: this.groupIdentities(item.identities).map(
            identity => identity.name
          ),
          identities: this.groupIdentities(item.identities),
          enrollments: item.enrollments,
          isLocked: item.isLocked,
          isBot: item.profile.isBot
        };
      });

      return formattedList;
    },
    groupIdentities(identities) {
      const icons = ["git", "github", "gitlab"];
      const groupedIdentities = identities.reduce((result, val) => {
        let source = val.source.toLowerCase();
        if (!icons.find(icon => icon === source)) {
          source = "others";
        }
        if (result[source]) {
          result[source].identities.push(val);
        } else {
          result[source] = {
            name: source,
            identities: [val]
          };
        }
        return result;
      }, {});

      return Object.values(groupedIdentities);
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
