<template>
  <v-data-table
    hide-default-header
    hide-default-footer
    :headers="headers"
    :items="individuals"
    :expanded.sync="expandedItems"
    item-key="id"
  >
    <template v-slot:item="{ item, expand, isExpanded }">
      <individual-entry
        :name="item.name"
        :organization="item.organization"
        :email="item.email"
        :sources="item.sources"
        :is-expanded="isExpanded"
        @expand="expand(!isExpanded)"
      />
    </template>
    <template v-slot:expanded-item="{ item }">
      <expanded-individual
        :enrollments="item.enrollments"
        :identities="item.identities"
        :name="item.name"
      />
    </template>
  </v-data-table>
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
    individuals: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      headers: [
        { value: 'name' },
        { value: 'email' },
        { value: 'sources' },
        { value: 'actions' }
      ],
      expandedItems: []
    }
  }
}
</script>
