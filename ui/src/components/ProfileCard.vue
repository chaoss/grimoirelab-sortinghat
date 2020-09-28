<template>
  <individual-card
    :name="name"
    :sources="sources"
    :is-locked="isLocked"
    :uuid="identities[0].identities[0].uuid"
    style="width: 600px"
  >
    <v-list-group>
      <template v-slot:activator>
        <v-list-item-title>
          Identities ({{ identitiesCount }})
        </v-list-item-title>
      </template>

      <v-list-group
        sub-group
        :key="source.name"
        v-for="source in identities"
        value="true"
      >
        <template v-slot:activator>
          <v-list-item-icon>
            <v-icon v-text="selectSourceIcon(source.name)" left />
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>{{ source.name }}</v-list-item-title>
          </v-list-item-content>
        </template>

        <v-list-item v-for="identity in source.identities" :key="identity.uuid">
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
    </v-list-group>

    <v-list-group>
      <template v-slot:activator>
        <v-list-item-content>
          <v-list-item-title>
            Organizations ({{ enrollments.length }})
          </v-list-item-title>
        </v-list-item-content>
      </template>

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
    },
    enrollments: {
      type: Array,
      required: true
    },
    isLocked: {
      type: Boolean,
      required: false,
      default: false
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
