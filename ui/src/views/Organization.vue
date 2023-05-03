<template>
  <v-main class="mt-md-3">
    <v-overlay :value="isLoading">
      <v-progress-circular indeterminate size="64"></v-progress-circular>
    </v-overlay>
    <v-container v-if="organization">
      <div class="section d-flex flex-column">
        <h1 class="header font-weight-medium text-h6 pa-8">
          {{ organization.name }}
          <v-btn
            text
            small
            outlined
            @click="confirmDelete(deleteOrganization, organization.name)"
          >
            <v-icon small left>mdi-delete</v-icon>
            Delete
          </v-btn>
        </h1>
        <v-row class="mt-0 mb-0">
          <v-col sm="12" md="4" class="border-right">
            <section class="pa-4 pt-2">
              <v-subheader class="d-flex justify-space-between">
                Teams
                <v-edit-dialog
                  large
                  @save="addTeam()"
                  @cancel="form.team = null"
                >
                  <v-btn text small outlined>
                    <v-icon small left>mdi-plus</v-icon>
                    Add
                  </v-btn>
                  <template v-slot:input>
                    <v-subheader class="pl-0">New team</v-subheader>
                    <v-text-field
                      v-model="form.team"
                      label="Name"
                      single-line
                      dense
                    ></v-text-field>
                  </template>
                </v-edit-dialog>
              </v-subheader>
              <v-treeview
                :items="teams.items"
                :load-children="loadChildren"
                :open.sync="teams.open"
                class="ml-2 mr-2"
                active-class="selected"
                expand-icon="mdi-chevron-down"
                activatable
                dense
                hoverable
                return-object
                @update:active="filterByTeam"
              >
                <template v-slot:append="{ item }">
                  <v-edit-dialog
                    large
                    @save="addTeam(item)"
                    @cancel="form.team = null"
                  >
                    <v-btn aria-label="Add team" small icon>
                      <v-icon small>mdi-plus</v-icon>
                    </v-btn>
                    <template v-slot:input>
                      <v-subheader class="pl-0">
                        New team in {{ item.name }}
                      </v-subheader>
                      <v-text-field
                        v-model="form.team"
                        label="Name"
                        single-line
                        dense
                      ></v-text-field>
                    </template>
                  </v-edit-dialog>
                  <v-btn
                    aria-label="Delete team"
                    small
                    icon
                    @click.stop="confirmDelete(deleteTeam, item.name)"
                  >
                    <v-icon small>mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-treeview>
              <p
                v-if="teams.items.length === 0"
                class="text--secondary font-italic ml-4"
              >
                No teams
              </p>
            </section>
          </v-col>
          <v-col sm="12" md="8" class="pl-md-0">
            <section class="pt-2">
              <v-tabs>
                <v-tab class="ml-4"> Details </v-tab>
                <v-tab>
                  Members
                  <v-chip x-small class="ml-2">
                    {{ totalMembers }}
                  </v-chip>
                </v-tab>
                <v-tab-item class="ma-4">
                  <v-list>
                    <v-subheader class="d-flex justify-space-between">
                      Domains
                      <v-edit-dialog
                        large
                        @save="addDomain"
                        @cancel="form.domain = null"
                      >
                        <v-btn text small outlined>
                          <v-icon small left>mdi-plus</v-icon>
                          Add
                        </v-btn>
                        <template v-slot:input>
                          <v-subheader class="pl-0">New domain</v-subheader>
                          <v-text-field
                            v-model="form.domain"
                            label="Domain"
                            single-line
                            dense
                          ></v-text-field>
                          <v-checkbox
                            v-model="form.isTopDomain"
                            label="Top domain"
                            dense
                          ></v-checkbox>
                        </template>
                      </v-edit-dialog>
                    </v-subheader>
                    <v-list-item
                      v-for="domain in organization.domains"
                      :key="domain.id"
                    >
                      <v-list-item-content>
                        <v-list-item-title>
                          {{ domain.domain }}
                          <v-chip
                            v-if="domain.isTopDomain"
                            class="ml-2 mb-1 primary--text"
                            color="#dceef9"
                            small
                          >
                            top domain
                          </v-chip>
                        </v-list-item-title>
                      </v-list-item-content>
                      <v-list-item-icon>
                        <v-btn
                          aria-label="Delete domain"
                          small
                          icon
                          @click="confirmDelete(deleteDomain, domain.domain)"
                        >
                          <v-icon small>mdi-delete</v-icon>
                        </v-btn>
                      </v-list-item-icon>
                    </v-list-item>
                  </v-list>
                </v-tab-item>
                <v-tab-item eager>
                  <individuals-table
                    class="mt-4"
                    hide-header
                    :fetch-page="fetchMembers"
                    :delete-item="deleteIndividual"
                    :merge-items="mergeIndividuals"
                    :unmerge-items="() => {}"
                    :move-item="() => {}"
                    :add-identity="() => {}"
                    :updateProfile="updateProfile"
                    :enroll="() => {}"
                    :fetch-organizations="() => {}"
                    :get-countries="() => {}"
                    :lock-individual="lockIndividual"
                    :unlock-individual="unlockIndividual"
                    :set-filters="filters"
                    :withdraw="() => {}"
                    :update-enrollment="() => {}"
                  />
                </v-tab-item>
              </v-tabs>
            </section>
          </v-col>
        </v-row>
      </div>
    </v-container>

    <v-container v-else-if="!isLoading">
      <v-alert text type="error">Organization {{ name }} not found </v-alert>
      <v-btn to="/" color="primary" depressed>
        <v-icon left dark>mdi-arrow-left</v-icon>
        Go to dashboard
      </v-btn>
    </v-container>

    <v-dialog v-model="dialog.isOpen" max-width="500">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p v-if="dialog.text" class="pt-2 pb-2 text-body-2">
            {{ dialog.text }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog"> Cancel </v-btn>
          <v-btn
            :color="dialog.color"
            id="confirm"
            depressed
            @click.stop="dialog.action"
          >
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-main>
</template>
<script>
import {
  getOrganization,
  getTeams,
  getPaginatedIndividuals,
} from "../apollo/queries";
import {
  deleteIdentity,
  merge,
  deleteOrganization,
  addDomain,
  deleteDomain,
  addTeam,
  deleteTeam,
  updateProfile,
  lockIndividual,
  unlockIndividual,
} from "../apollo/mutations";
import IndividualsTable from "../components/IndividualsTable.vue";

export default {
  name: "Organization",
  components: { IndividualsTable },
  data() {
    return {
      organization: null,
      isLoading: true,
      teams: {
        items: [],
        open: [],
      },
      totalMembers: 0,
      dialog: {
        isOpen: false,
        title: null,
        action: null,
        text: null,
        color: "primary",
      },
      form: {
        domain: null,
        isTopDomain: true,
        team: null,
      },
      filters: null,
    };
  },
  computed: {
    name() {
      return decodeURIComponent(this.$route.params.name);
    },
  },
  methods: {
    async fetchOrganization(name) {
      try {
        const response = await getOrganization(this.$apollo, name);
        if (response.data.organizations.entities.length > 0) {
          this.organization = response.data.organizations.entities[0];
        }
      } catch (error) {
        this.$logger.error(error);
      }
    },
    confirmDelete(action, id) {
      Object.assign(this.dialog, {
        isOpen: true,
        action: () => action(id),
        title: `Delete ${id}?`,
        color: "error",
      });
    },
    async deleteOrganization() {
      try {
        const response = await deleteOrganization(this.$apollo, this.name);
        if (response && !response.errors) {
          this.$router.push({ name: "Dashboard" });
        }
      } catch (error) {
        Object.assign(this.dialog, { text: error });
      }
    },
    async addDomain() {
      if (!this.form.domain) return;

      try {
        const response = await addDomain(
          this.$apollo,
          this.form.domain,
          this.form.isTopDomain,
          this.name
        );
        this.organization.domains.push(response.data.addDomain.domain);
        this.form.domain = null;
      } catch (error) {
        Object.assign(this.dialog, {
          isOpen: true,
          title: "Error creating domain",
          text: this.$getErrorMessage(error),
        });
      }
    },
    async deleteDomain(domain) {
      try {
        const response = await deleteDomain(this.$apollo, domain);
        if (response && !response.errors) {
          const index = this.organization.domains.findIndex(
            (item) => item.domain === domain
          );
          this.organization.domains.splice(index, 1);
          this.closeDialog();
        }
      } catch (error) {
        Object.assign(this.dialog, { text: error });
      }
    },
    async fetchTeams(parent) {
      const response = await getTeams(this.$apollo, {
        organization: this.organization?.name,
        parent: parent,
      });

      const teams = response.data.teams.entities.map((team) => {
        return {
          id: team.id,
          name: team.name,
          children: team.numchild > 0 ? [] : undefined,
        };
      });

      return teams;
    },
    async addTeam(parent) {
      try {
        await addTeam(this.$apollo, this.form.team, this.name, parent?.name);
        if (parent) {
          parent.children = parent.children || [];
          parent.children.push({
            name: this.form.team,
            children: undefined,
          });
        } else {
          this.teams.items.push({
            name: this.form.team,
            children: undefined,
          });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          isOpen: true,
          title: "Error creating team",
          text: this.$getErrorMessage(error),
        });
      }
      this.form.team = null;
    },
    async deleteTeam(team) {
      try {
        const response = await deleteTeam(this.$apollo, team, this.name);
        if (response && !response.errors) {
          this.removeTeamNode(team);
          this.closeDialog();
        }
      } catch (error) {
        Object.assign(this.dialog, { text: error });
      }
    },
    removeTeamNode(name, teams = this.teams.items) {
      teams.every((child, index) => {
        if (child.name === name) {
          teams.splice(index, 1);
          return false;
        } else if (child.children) {
          this.removeTeamNode(name, child.children);
        }
        return true;
      });
    },
    async loadChildren(parent) {
      parent.children = await this.fetchTeams(parent.name);
    },
    async fetchMembers(page = 1, items = 10, filters = {}, orderBy) {
      if (!filters.enrollment) {
        filters = Object.assign(filters, {
          enrollment: this.organization.name,
        });
      }
      const response = await getPaginatedIndividuals(
        this.$apollo,
        page,
        items,
        filters,
        orderBy
      );
      if (response && !response.erros) {
        this.totalMembers = response.data.individuals.pageInfo.totalResults;
      }
      return response;
    },
    filterByTeam(selected) {
      if (selected[0]) {
        this.$nextTick(
          () =>
            (this.filters = `enrollment:"${selected[0].name}" enrollmentParentOrg:"${this.name}"`)
        );
      } else {
        this.$nextTick(() => (this.filters = null));
      }
    },
    async deleteIndividual(uuid) {
      const response = await deleteIdentity(this.$apollo, uuid);
      return response;
    },
    async mergeIndividuals(fromUuids, toUuid) {
      const response = await merge(this.$apollo, fromUuids, toUuid);
      return response;
    },
    async lockIndividual(uuid) {
      const response = await lockIndividual(this.$apollo, uuid);
      return response;
    },
    async unlockIndividual(uuid) {
      const response = await unlockIndividual(this.$apollo, uuid);
      return response;
    },
    async updateProfile(data, uuid) {
      const response = updateProfile(this.$apollo, data, uuid);
      return response;
    },
    closeDialog() {
      Object.assign(this.dialog, {
        isOpen: false,
        title: "",
        action: null,
        color: "primary",
      });
    },
  },
  async mounted() {
    await this.fetchOrganization(this.name);
    this.teams.items = await this.fetchTeams();
    this.isLoading = false;
  },
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";

::v-deep .v-treeview-node__toggle,
::v-deep .v-treeview-node__level {
  font-size: 16px;
  width: 16px;
}

::v-deep .v-treeview-node {
  cursor: pointer;
}

.border-right {
  border-right: thin solid rgba(0, 0, 0, 0.08);
}

::v-deep .v-tab {
  font-weight: 500;
  font-size: 1rem;
  letter-spacing: 0.0071rem;
  text-transform: none;
  min-width: 80px;
}

.v-tabs-bar {
  height: 40px;
}

.v-subheader {
  font-weight: 500;
  font-size: 1rem;
  letter-spacing: 0.0071rem;
}

::v-deep .v-small-dialog,
::v-deep .v-small-dialog__activator {
  display: inline-block;
}

.container {
  // height: calc(100% - 24px);
  height: 100%;

  .section {
    min-height: 100%;
  }
}

@media (max-width: 1268px) {
  .container {
    max-width: 100%;
  }
}
</style>
