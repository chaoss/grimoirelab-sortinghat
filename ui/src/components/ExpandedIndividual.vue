<template>
  <td :class="{ compact: compact }" colspan="4">
    <v-subheader>Identities ({{ identitiesCount }})</v-subheader>
    <v-list
      v-for="(source, sourceIndex) in sortSources(identities, 'name')"
      :key="source.name"
      class="indented"
    >
      <v-list-item
        v-for="(identity, index) in sortSources(source.identities, 'source')"
        :key="identity.uuid"
      >
        <v-list-item-icon v-if="index === 0 && !compact">
          <v-icon>
            {{ selectSourceIcon(source.name) }}
          </v-icon>
        </v-list-item-icon>

        <v-list-item-action v-else-if="!compact"></v-list-item-action>

        <v-list-item-content>
          <identity
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
            :source="identity.source || source.name"
          />
        </v-list-item-content>

        <v-list-item-action v-if="!compact">
          <v-tooltip
            bottom
            transition="expand-y-transition"
            open-delay="200"
          >
            <template v-slot:activator="{ on }">
              <v-btn
                icon
                :disabled="identity.uuid === uuid"
                v-on="on"
                @click="$emit('unmerge', [identity.uuid, uuid])"
              >
                <v-icon>
                  mdi-call-split
                </v-icon>
              </v-btn>
            </template>
            <span>Split identity</span>
          </v-tooltip>
        </v-list-item-action>

      </v-list-item>
      <v-divider
        inset
        v-if="sourceIndex !== identities.length - 1 && !compact"
      ></v-divider>
    </v-list>

    <v-divider v-if="!compact" inset class="divider"></v-divider>

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
  name: "ExpandedIndividual",
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
    },
    compact: {
      type: Boolean,
      required: false,
      default: false
    },
    uuid: {
      type: String,
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
    },
    sortSources(identities, property) {
      return identities.slice().sort((a, b) => {
        const sourceA = a[property].toLowerCase();
        const sourceB = b[property].toLowerCase();

        return sourceA.localeCompare(sourceB);
      });
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
<style lang="scss" scoped>
td {
  padding-left: 75px;
  border-bottom: thin solid rgba(0, 0, 0, 0.12);
}

.indented {
  margin: 0 40px;
}

.v-application--is-ltr .v-divider--inset:not(.v-divider--vertical).divider {
  width: calc(100% - 30px);
  max-width: calc(100% - 30px);
  margin-left: 30px;
}

.compact {
  padding-left: 0;
  border-bottom: 0;
  background-color: #ffffff;
  font-size: 0.9rem;
  line-height: 1rem;
  padding: 0;

  .v-list-item__content,
  .v-sheet--tile {
    padding: 0;
  }

  ::v-deep .uuid {
    display: none;
  }

  ::v-deep .indented {
    padding: 0;
    margin: 0;
  }
}
</style>
