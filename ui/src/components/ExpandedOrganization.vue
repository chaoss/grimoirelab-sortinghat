<template>
  <td colspan="3">
    <v-list dense>
      <v-subheader>Domains ({{ domains.length }})</v-subheader>
      <v-list-item v-for="(item, index) in domains" :key="index">
        <v-list-item-content>
          <v-list-item-title>{{ item.domain }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </td>
</template>

<script>
export default {
  name: "ExpandedOrganization",
  props: {
    domains: {
      type: Array,
      required: true
    }
  }
};
</script>
