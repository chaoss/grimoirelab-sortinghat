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

    <v-subheader>Organizations ({{ enrollments.length }})</v-subheader>

    <v-list>
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
      return dateTime.split('T')[0]
    }
  }
};
</script>
