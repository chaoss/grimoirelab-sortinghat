<template>
  <individual-card :name="name" style="width: 600px">
    <v-subheader>Identities</v-subheader>

    <v-list-group
      :prepend-icon="selectSourceIcon(source.name)"
      :key="source.name"
      v-for="source in identities"
      value="true"
    >
      <template v-slot:activator>
        <v-list-item-content>
          <v-list-item-title>{{ source.name }}</v-list-item-title>
        </v-list-item-content>
      </template>

      <v-list-item
        v-for="identity in source.identities"
        :key="identity.uuid"
        @click=""
      >
        <v-list-item-content>
          <identity
            v-if="source.name.toLowerCase() !== 'others'"
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
          />
          <identity
            v-else
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
            :source="identity.source"
          />
        </v-list-item-content>
      </v-list-item>
    </v-list-group>
  </individual-card>
</template>

<script>
import Identity from "./Identity.vue";
import IndividualCard from "./IndividualCard.vue";

export default {
  name: "profilecard",
  components: {
    Identity,
    IndividualCard
  },
  props: {
    name: {
      type: String,
      required: true
    },
    identities: {
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
    }
  }
};
</script>
