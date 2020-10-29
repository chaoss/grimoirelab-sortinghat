<template>
  <tr>
    <td class="text--body-1">{{ name }}</td>
    <td class="text-right text--secondary">{{ enrollments }}</td>
    <td class="text-right" width="40">
      <v-btn icon @click.stop="$emit('expand')">
        <v-icon>
          {{ isExpanded ? "mdi-chevron-up" : "mdi-chevron-down" }}
        </v-icon>
      </v-btn>
    </td>
  </tr>
</template>

<script>
export default {
  name: "OrganizationEntry",
  props: {
    name: {
      type: String,
      required: true
    },
    enrollments: {
      type: Number,
      required: true
    },
    isExpanded: {
      type: Boolean,
      required: true
    }
  }
};
</script>
