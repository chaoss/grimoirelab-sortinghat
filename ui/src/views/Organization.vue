<template>
  <v-container class="mt-md-3">
    <loading-spinner
      v-if="$apollo.queries.organizations.loading"
      label="Loading"
    />
    <v-container v-else-if="organization">
      <div class="section d-flex flex-column">
        <h1 class="header font-weight-medium text-h6 pa-8">
          {{ organization.name }}
          <v-btn
            size="small"
            variant="outlined"
            @click="confirmDelete(deleteOrganization, organization.name)"
          >
            <v-icon size="small" start>mdi-delete</v-icon>
            Delete
          </v-btn>
        </h1>
        <v-row class="mt-0 mb-0">
          <v-col sm="12" md="4" class="border-right">
            <section class="pa-4 pt-2">
              <v-list-subheader
                class="d-flex justify-space-between text-subtitle-2 font-weight-medium ml-4"
              >
                Teams
                <edit-dialog
                  activator="button"
                  label="Team name"
                  @save="addTeam($event)"
                />
              </v-list-subheader>
              <v-list
                v-model:opened="teams.open"
                color="primary"
                density="compact"
                nav
                @update:selected="filterByTeam"
              >
                <div v-for="team in teams.items" :key="team.id">
                  <v-list-group v-if="team.children" :value="team.name">
                    <template v-slot:activator="{ props }">
                      <v-list-item
                        v-bind="props"
                        @clickOnce="loadChildren(team)"
                        :value="team"
                      >
                        <v-list-item-title
                          class="d-flex justify-space-between align-center"
                        >
                          {{ team.name }}
                          <div>
                            <v-menu
                              v-model="team.menu"
                              :close-on-content-click="false"
                            >
                              <template v-slot:activator="{ props }">
                                <v-btn
                                  v-bind="props"
                                  aria-label="Add team"
                                  density="comfortable"
                                  icon="mdi-plus"
                                  size="small"
                                  variant="text"
                                />
                              </template>
                              <v-card min-width="200">
                                <v-card-text>
                                  <v-text-field
                                    v-model="form.team"
                                    label="Team name"
                                    color="primary"
                                    density="compact"
                                    hide-details
                                    single-line
                                  />
                                </v-card-text>
                                <v-card-actions>
                                  <v-btn
                                    @click="
                                      team.menu = false;
                                      form.team = '';
                                    "
                                  >
                                    Cancel
                                  </v-btn>
                                  <v-btn
                                    @click="
                                      addTeam(form.team, team);
                                      team.menu = false;
                                    "
                                  >
                                    Save
                                  </v-btn>
                                </v-card-actions>
                              </v-card>
                            </v-menu>
                            <v-btn
                              aria-label="Delete team"
                              density="comfortable"
                              icon="mdi-delete"
                              size="small"
                              variant="text"
                              @click.stop="confirmDelete(deleteTeam, team.name)"
                            />
                          </div>
                        </v-list-item-title>
                      </v-list-item>
                    </template>
                    <v-list-item
                      v-for="child in team.children"
                      :key="child.id"
                      :value="child"
                    >
                      <v-list-item-title
                        class="d-flex justify-space-between align-center"
                      >
                        {{ child.name }}
                        <v-btn
                          aria-label="Delete team"
                          class="mr-7"
                          density="comfortable"
                          icon="mdi-delete"
                          size="small"
                          variant="text"
                          @click.stop="confirmDelete(deleteTeam, child.name)"
                        />
                      </v-list-item-title>
                    </v-list-item>
                  </v-list-group>
                  <v-list-item v-else :value="team">
                    <v-list-item-title
                      class="d-flex justify-space-between align-center"
                    >
                      {{ team.name }}
                      <div>
                        <v-menu
                          v-model="team.menu"
                          :close-on-content-click="false"
                        >
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              aria-label="Add team"
                              density="comfortable"
                              icon="mdi-plus"
                              size="small"
                              variant="text"
                            />
                          </template>
                          <v-card min-width="200">
                            <v-card-text>
                              <v-text-field
                                v-model="form.team"
                                label="Team name"
                                color="primary"
                                density="compact"
                                hide-details
                                single-line
                              />
                            </v-card-text>
                            <v-card-actions>
                              <v-btn
                                @click="
                                  team.menu = false;
                                  form.team = '';
                                "
                              >
                                Cancel
                              </v-btn>
                              <v-btn
                                @click="
                                  addTeam(form.team, team);
                                  team.menu = false;
                                "
                              >
                                Save
                              </v-btn>
                            </v-card-actions>
                          </v-card>
                        </v-menu>
                        <v-btn
                          aria-label="Delete team"
                          class="mr-7"
                          density="comfortable"
                          icon="mdi-delete"
                          size="small"
                          variant="text"
                          @click.stop="confirmDelete(deleteTeam, team.name)"
                        />
                      </div>
                    </v-list-item-title>
                  </v-list-item>
                </div>
              </v-list>
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
              <v-tabs v-model="tab" color="primary">
                <v-tab :value="1" class="ml-4">Details</v-tab>
                <v-tab :value="2">
                  Members
                  <v-chip size="small" class="ml-2">
                    {{ totalMembers }}
                  </v-chip>
                </v-tab>
              </v-tabs>
              <v-window v-model="tab">
                <v-window-item :value="1">
                  <v-container>
                    <v-list>
                      <v-list-subheader
                        class="d-flex justify-space-between text-subtitle-2 font-weight-medium"
                      >
                        Domains
                        <v-menu v-model="menu" :close-on-content-click="false">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              size="small"
                              variant="outlined"
                            >
                              <v-icon start>mdi-plus</v-icon>
                              Add
                            </v-btn>
                          </template>
                          <v-card min-width="200">
                            <v-card-text>
                              <v-list-subheader
                                class="pl-0 text-subtitle-2 font-weight-medium"
                              >
                                New domain
                              </v-list-subheader>
                              <v-text-field
                                v-model="form.domain"
                                label="Domain"
                                single-line
                                density="compact"
                              ></v-text-field>
                              <v-checkbox
                                v-model="form.isTopDomain"
                                label="Top domain"
                                density="compact"
                                hide-details
                              ></v-checkbox>
                            </v-card-text>
                            <v-card-actions>
                              <v-spacer></v-spacer>
                              <v-btn
                                size="small"
                                @click="
                                  menu = false;
                                  form.domain = null;
                                "
                              >
                                Cancel
                              </v-btn>
                              <v-btn size="small" @click="addDomain">
                                Save
                              </v-btn>
                            </v-card-actions>
                          </v-card>
                        </v-menu>
                      </v-list-subheader>
                      <v-list-item
                        v-for="domain in organization.domains"
                        :key="domain.id"
                      >
                        <v-list-item-title>
                          {{ domain.domain }}
                          <v-chip
                            v-if="domain.isTopDomain"
                            class="ml-2"
                            color="primary"
                            size="small"
                          >
                            top domain
                          </v-chip>
                        </v-list-item-title>
                        <template v-slot:append>
                          <v-btn
                            aria-label="Delete domain"
                            size="small"
                            variant="text"
                            icon
                            @click="confirmDelete(deleteDomain, domain.domain)"
                          >
                            <v-icon small>mdi-delete</v-icon>
                          </v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                    <v-list>
                      <v-list-subheader
                        class="d-flex justify-space-between text-subtitle-2 font-weight-medium"
                      >
                        Aliases
                        <edit-dialog
                          activator="button"
                          label="New alias"
                          @save="addAlias($event)"
                        />
                      </v-list-subheader>
                      <v-list-item
                        v-for="(alias, i) in organization.aliases"
                        :key="i"
                      >
                        <v-list-item-title>
                          {{ alias.alias }}
                        </v-list-item-title>
                        <template v-slot:append>
                          <v-btn
                            aria-label="Delete alias"
                            size="small"
                            variant="text"
                            icon="mdi-delete"
                            @click="confirmDelete(deleteAlias, alias.alias)"
                          >
                          </v-btn>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-container>
                </v-window-item>

                <v-window-item :value="2" eager>
                  <v-container class="pa-0">
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
                      :recommend-matches="() => {}"
                      :set-filters="filters"
                      :withdraw="() => {}"
                      :update-enrollment="() => {}"
                      ref="membersTable"
                    />
                  </v-container>
                </v-window-item>
              </v-window>
            </section>
          </v-col>
        </v-row>
      </div>
    </v-container>

    <v-container v-if="error">
      <v-alert text type="error">{{ error }} </v-alert>
      <v-btn to="/" color="primary" depressed>
        <v-icon left dark>mdi-arrow-left</v-icon>
        Go to dashboard
      </v-btn>
    </v-container>

    <generic-modal v-model:is-open="modalProps.isOpen" v-bind="modalProps" />
  </v-container>
</template>
<script>
import {
  getTeams,
  getPaginatedIndividuals,
  GET_ORGANIZATION,
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
  addAlias,
  deleteAlias,
  mergeOrganizations,
} from "../apollo/mutations";
import IndividualsTable from "../components/IndividualsTable.vue";
import EditDialog from "../components/EditDialog.vue";
import LoadingSpinner from "../components/LoadingSpinner.vue";
import GenericModal from "../components/GenericModal.vue";
import useModal from "../composables/useModal";

export default {
  name: "Organization",
  components: { IndividualsTable, EditDialog, LoadingSpinner, GenericModal },
  apollo: {
    organizations() {
      return {
        query: GET_ORGANIZATION,
        variables: {
          filters: {
            name: this.name,
          },
        },
        async result(result) {
          if (result.data?.organizations.entities.length === 1) {
            this.organization = Object.assign(
              {},
              result.data.organizations.entities[0]
            );
            this.teams.items = await this.fetchTeams();
          } else if (result.errors) {
            this.error = this.$getErrorMessage(result.errors[0]);
          } else {
            this.error = `Organization ${this.name} not found`;
          }
        },
      };
    },
  },
  setup() {
    const { modalProps, openModal, closeModal } = useModal();
    return { modalProps, openModal, closeModal };
  },
  data() {
    return {
      organization: null,
      isLoading: true,
      teams: {
        items: [],
        open: [],
        menu: false,
      },
      totalMembers: 0,
      form: {
        domain: null,
        isTopDomain: true,
        team: null,
        alias: null,
      },
      filters: null,
      tab: null,
      menu: false,
      error: null,
    };
  },
  computed: {
    name() {
      return decodeURIComponent(this.$route.params.name);
    },
  },
  methods: {
    confirmDelete(action, id) {
      this.openModal({
        action: () => action(id),
        title: `Delete ${id}?`,
        actionButtonColor: "error",
      });
    },
    async deleteOrganization() {
      try {
        const response = await deleteOrganization(this.$apollo, this.name);
        if (response && !response.errors) {
          this.$router.push({ name: "Dashboard" });
        }
      } catch (error) {
        this.openModal({ text: this.$getErrorMessage(error) });
      }
    },
    async addDomain() {
      this.menu = false;
      if (!this.form.domain) return;

      try {
        const response = await addDomain(
          this.$apollo,
          this.form.domain,
          this.form.isTopDomain,
          this.name
        );
        this.organization.domains = [
          ...this.organization.domains,
          response.data.addDomain.domain,
        ];
        this.form.domain = null;
      } catch (error) {
        this.openModal({
          title: "Error creating domain",
          text: this.$getErrorMessage(error),
        });
      }
    },
    async deleteDomain(domain) {
      try {
        const response = await deleteDomain(this.$apollo, domain);
        if (response && !response.errors) {
          const domains = [...this.organization.domains];
          const index = domains.findIndex((item) => item.domain === domain);
          domains.splice(index, 1);
          this.organization.domains = domains;
        }
      } catch (error) {
        this.openModal({ text: this.$getErrorMessage(error) });
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
    async addTeam(team, parent) {
      try {
        await addTeam(this.$apollo, team, this.name, parent?.name);
        if (parent) {
          parent.children = parent.children || [];
          parent.children.push({
            name: this.form.team,
            children: undefined,
          });
        } else {
          this.teams.items.push({
            name: team,
            children: undefined,
          });
        }
      } catch (error) {
        this.openModal({
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
        }
      } catch (error) {
        this.openModal({ text: this.$getErrorMessage(error) });
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
          enrollment: this.name,
        });
      }
      const response = await getPaginatedIndividuals(
        this.$apollo,
        page,
        items,
        filters,
        orderBy
      );
      if (response && !response.errors) {
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
    async addAlias(alias) {
      if (!alias) return;
      const response = await addAlias(this.$apollo, alias, this.name);

      if (response.errors) {
        const modalData = {
          title: "Error creating alias",
          text: this.$getErrorMessage(response.errors[0]),
        };
        const orgAlreadyExists = response.errors.find((error) => {
          return (
            error.extensions.code === 2 &&
            error.message.includes("Organization")
          );
        });
        const aliasAlreadyExists = response.errors.find((error) => {
          return error.extensions.code === 2 && error.message.includes("Alias");
        });
        if (orgAlreadyExists) {
          Object.assign(modalData, {
            action: () => this.mergeOrgs(alias, this.name),
            dismissButtonLabel: "Cancel",
            actionButtonLabel: "Merge",
            text: (modalData.text += `. Click 'merge' to turn it into an alias of '${this.name}'.`),
          });
        } else if (aliasAlreadyExists) {
          Object.assign(modalData, {
            action: () => this.mergeOrgs(alias, this.name),
            dismissButtonLabel: "Cancel",
            actionButtonLabel: "Merge",
            text: (modalData.text += `. Click 'merge' to turn it and its organization into aliases of '${this.name}'.`),
          });
        }
        this.openModal(modalData);
      } else {
        this.organization.aliases = [
          ...this.organization.aliases,
          response.data.addAlias.alias,
        ];
      }
    },
    async mergeOrgs(fromOrg, toOrg) {
      try {
        const response = await mergeOrganizations(this.$apollo, fromOrg, toOrg);
        if (response && !response.errors) {
          this.organization = Object.assign(
            {},
            response.data.mergeOrganizations.organization
          );
          this.$refs.membersTable.queryIndividuals();
        }
      } catch (error) {
        this.openModal({ text: this.$getErrorMessage(error) });
      }
    },
    async deleteAlias(alias) {
      try {
        const response = await deleteAlias(this.$apollo, alias);
        if (response && !response.errors) {
          const aliases = [...this.organization.aliases];
          const index = aliases.findIndex((item) => item.alias === alias);
          aliases.splice(index, 1);
          this.organization.aliases = aliases;
        }
      } catch (error) {
        this.openModal({ text: this.$getErrorMessage(error) });
      }
    },
  },
};
</script>

<style lang="scss" scoped>
@use "../styles/index.scss";

:deep(.v-treeview-node__toggle),
:deep(.v-treeview-node__level) {
  font-size: 16px;
  width: 16px;
}

:deep(.v-treeview-node) {
  cursor: pointer;
}

.border-right {
  border-right: thin solid rgba(0, 0, 0, 0.08);
}

:deep(.v-tab) {
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

:deep(.v-small-dialog),
:deep(.v-small-dialog__activator) {
  display: inline-block;
}

.v-container {
  height: calc(100% - 24px);
  height: 100%;

  .section {
    min-height: calc(100% - 80px);
  }
}

@media (max-width: 1268px) {
  .container {
    max-width: 100%;
  }
}

:deep(.v-list-item__append) > .v-icon ~ .v-list-item__spacer {
  width: 4px;
}
</style>
