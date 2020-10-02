<template>
  <tr>
    <td width="25%">
      <v-list-item>
        <v-list-item-avatar color="grey">
          {{ getNameInitials }}
        </v-list-item-avatar>

        <v-list-item-content>
          <v-list-item-title>{{ name }}</v-list-item-title>
          <v-list-item-subtitle>{{ organization }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </td>
    <td class="text-center">
      {{ email }}
    </td>
    <td class="text-right">
      <v-icon
        v-for="source in sources"
        :key="source.name"
        v-text="selectSourceIcon(source)"
        left
        right
      />
    </td>
    <td width="50">
      <v-btn icon @click="$emit('expand')">
        <v-icon>{{ isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
      </v-btn>
    </td>
  </tr>
</template>
<script>
export default {
  name: "IndividualEntry",
  props: {
    name: {
      type: String,
      required: true
    },
    organization: {
      type: String,
      required: false
    },
    email: {
      type: String,
      required: true
    },
    sources: {
      type: Array,
      required: false
    },
    isExpanded: {
      type: Boolean,
      required: true
    }
  },
  computed: {
    getNameInitials: function() {
      var names = this.name.split(" ");
      var initials = names[0].substring(0, 1).toUpperCase();

      if (names.length > 1) {
        initials += names[names.length - 1].substring(0, 1).toUpperCase();
      }

      return initials;
    }
  },
  methods: {
    selectSourceIcon(source) {
      const datasource = source.toLowerCase();

      if (datasource === "others") {
        return "mdi-account-multiple";
      } else {
        return `mdi-${datasource}`;
      }
    }
  }
}
</script>
