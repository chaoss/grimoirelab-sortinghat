<template>
  <td colspan="3">
    <v-subheader>Identities ({{ identitiesCount }})</v-subheader>
    <v-list
      v-for="(source, sourceIndex) in identities"
      :key="source.name"
      class="indented"
    >
      <v-list-item
        v-for="(identity, index) in source.identities"
        :key="identity.uuid"
      >
        <v-list-item-icon v-if="index === 0">
          <v-icon>
            {{ selectSourceIcon(source.name) }}
          </v-icon>
        </v-list-item-icon>

        <v-list-item-action v-else></v-list-item-action>

        <v-list-item-content>
          <identity
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
            :source="identity.source || source.name"
          />
        </v-list-item-content>
      </v-list-item>
      <v-divider inset v-if="sourceIndex !== identities.length - 1"></v-divider>
    </v-list>

    <v-divider inset class="divider"></v-divider>

    <v-list>
      <v-subheader>Organizations ({{ enrollments.length }})</v-subheader>

      <v-list-item
        v-for="enrollment in enrollments"
        :key="enrollment.organization.id"
      >
        <v-list-item-content>
          <v-row no-gutters>
            <v-col class="ma-2 text-center">
              <span>{{ enrollment.organization.name }}</span>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span>{{ formatDate(enrollment.start) }}</span>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span>{{ formatDate(enrollment.end) }}</span>
            </v-col>
          </v-row>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </td>
</template>

<script>
import Identity from "./Identity.vue";

export default {
  name: "profilecard",
  components: {
    Identity
  },
  props: {
    identities: {
      type: Array,
      required: true
    },
    enrollments: {
      type: Array,
      required: true
    }
  },
  methods: {
    selectSourceIcon(source) {
      var datasource = source.toLowerCase();

      if (datasource === "github") {
        return "mdi-github";
      } else if (datasource === "git") {
        return "mdi-git";
      } else if (datasource === "gitlab") {
        return "mdi-gitlab";
      } else if (datasource === "others") {
        return "mdi-account-multiple";
      }
    },
    formatDate(dateTime) {
      return dateTime.split("T")[0];
    }
  },
  computed: {
    identitiesCount() {
      return this.identities.reduce((a, b) => a + b.identities.length, 0);
    },
    sources() {
      return this.identities.map(identity => identity.name);
    }
  }
};
</script>
<style scoped>
td {
  padding-left: 75px;
  border-bottom: thin solid rgba(0, 0, 0, 0.12);
}

.indented {
  margin-left: 40px;
}

.v-application--is-ltr .v-divider--inset:not(.v-divider--vertical).divider {
  width: calc(100% - 30px);
  max-width: calc(100% - 30px);
  margin-left: 30px;
}
</style>
