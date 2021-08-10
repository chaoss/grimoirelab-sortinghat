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
    <v-list dense>
      <v-subheader>
        Teams ({{ teams.length }}<span v-if="teams.length > 0">+</span>)
        <v-btn depressed small height="34" @click.stop="openModal" text>
          View all
        </v-btn>
      </v-subheader>
      <v-list-item v-for="(item, index) in teams" :key="index">
        <v-list-item-content>
          <v-list-item-title>{{ item.name }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
    <team-modal
      :is-open.sync="modal.open"
      :organization="organization"
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
      required: true
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
  methods: {
    openModal() {
      Object.assign(this.modal, { open: true });
    },
    async getTeams() {
      const filters = { organization: this.organization };
      const response = await this.fetchTeams(filters);
      this.teams = response.data.teams.entities;
    }
  },
  async created() {
    await this.getTeams();
  }
};
</script>
