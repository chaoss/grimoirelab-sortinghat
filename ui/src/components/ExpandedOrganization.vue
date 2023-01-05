<template>
  <td colspan="3">
    <v-list v-if="!isGroup" dense>
      <v-subheader>Domains ({{ domains.length }})</v-subheader>
      <v-list-item v-for="(item, index) in domains" :key="index">
        <v-list-item-content>
          <v-list-item-title>{{ item.domain }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <v-list dense>
      <v-subheader>
        Teams ({{ teams.length }}<span v-if="hasSubteams">+</span>)
        <v-btn plain small height="34" @click.stop="openModal" text>
          View all
        </v-btn>
      </v-subheader>
      <v-list-item v-for="(item, index) in teams" :key="index">
        <v-list-item-content>
          <v-list-item-title class="team">
            <span class="team__name">{{ item.name }}</span>
            <v-tooltip bottom transition="expand-y-transition" open-delay="200">
              <template v-slot:activator="{ on }">
                <v-btn
                  small
                  depressed
                  color="transparent"
                  v-on="on"
                  @click.stop="
                    $emit('getEnrollments', {
                      enrollment: item.name,
                      parentOrg: organization
                    })
                  "
                >
                  {{ getEnrolledIndividuals(item.enrollments) }}
                  <v-icon small right>
                    mdi-account-multiple
                  </v-icon>
                </v-btn>
              </template>
              <span>Enrollments</span>
            </v-tooltip>
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <team-modal
      :is-open.sync="modal.open"
      :parent="organization"
      :is-group="isGroup"
      :add-team="addTeam"
      :delete-team="deleteTeam"
      :fetch-teams="fetchTeams"
      @updateTeams="getTeams"
    />
  </td>
</template>

<script>
import TeamModal from "./TeamModal.vue";

export default {
  name: "ExpandedOrganization",
  components: {
    TeamModal
  },
  props: {
    domains: {
      type: Array,
      required: false
    },
    organization: {
      type: String,
      required: true
    },
    addTeam: {
      type: Function,
      required: true
    },
    deleteTeam: {
      type: Function,
      required: true
    },
    fetchTeams: {
      type: Function,
      required: true
    },
    isGroup: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data() {
    return {
      teams: [],
      modal: {
        open: false
      }
    };
  },
  computed: {
    hasSubteams() {
      return this.teams.some(team => team.numchild > 0);
    }
  },
  methods: {
    openModal() {
      Object.assign(this.modal, { open: true });
    },
    async getTeams() {
      let filters = { organization: this.organization };
      if (this.isGroup) {
        filters = { parent: this.organization };
      }
      const response = await this.fetchTeams(filters);
      this.teams = response.data.teams.entities;
    },
    getEnrolledIndividuals(enrollments) {
      if (!enrollments) {
        return 0;
      }
      const uniqueIndividuals = new Set(
        enrollments.map(item => item.individual.mk)
      );

      return uniqueIndividuals.size;
    }
  },
  async created() {
    await this.getTeams();
  }
};
</script>
<style lang="scss" scoped>
.team {
  display: inline-flex;
  align-items: center;

  &__name {
    width: 44%;
    white-space: break-spaces;
  }
}
</style>
