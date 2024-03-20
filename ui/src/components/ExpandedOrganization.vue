<template>
  <td colspan="3" class="pa-1">
    <p class="ma-3 text-medium-emphasis ml-6" v-if="teams.length === 0">
      No teams
    </p>
    <v-list v-model:opened="openTeams" density="compact" nav>
      <div v-for="team in teams" :key="team.id">
        <v-list-group v-if="team.children" :value="team.name">
          <template v-slot:activator="{ props }">
            <v-list-item
              v-bind="props"
              draggable="true"
              @click.once="loadChildren(team)"
              @dragstart="($event) => startDrag(organization, team, $event)"
              @drop.stop="onDrop($event, team)"
              @dragover.prevent="isDropZone($event, true)"
              @dragenter.prevent="isDropZone($event, true)"
              @dragleave.prevent="isDropZone($event, false)"
            >
              <v-list-item-title
                class="d-flex justify-space-between align-center"
              >
                {{ team.name }}
                <div>
                  <v-btn
                    class="mr-9"
                    variant="text"
                    @click.stop="
                      $emit('getEnrollments', {
                        enrollment: team.name,
                        parentOrg: organization,
                      })
                    "
                  >
                    {{ team.enrollments }}
                    <v-icon end> mdi-account-multiple </v-icon>
                  </v-btn>
                  <v-menu :close-on-content-click="false">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        v-bind="props"
                        class="ml-2"
                        density="comfortable"
                        icon="mdi-dots-vertical"
                        variant="text"
                        @click.stop
                      />
                    </template>
                    <v-list density="compact">
                      <v-menu v-model="menu" :close-on-content-click="false">
                        <template v-slot:activator="{ props }">
                          <v-list-item v-bind="props">
                            <v-list-item-title>Add a team</v-list-item-title>
                          </v-list-item>
                        </template>
                        <v-card min-width="200">
                          <v-card-text>
                            <v-text-field
                              v-model="newTeam"
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
                                menu = false;
                                newTeam = '';
                              "
                            >
                              Cancel
                            </v-btn>
                            <v-btn @click="createTeam(team)"> Save </v-btn>
                          </v-card-actions>
                        </v-card>
                      </v-menu>
                      <v-list-item @click="confirmDelete(team)">
                        <v-list-item-title>Delete team</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </div>
              </v-list-item-title>
            </v-list-item>
          </template>
          <v-list-item
            v-for="child in team.children"
            :key="child.id"
            draggable="true"
            @dragstart="($event) => startDrag(organization, child, $event)"
            @drop.stop="onDrop($event, child)"
            @dragover.prevent="isDropZone($event, true)"
            @dragenter.prevent="isDropZone($event, true)"
            @dragleave.prevent="isDropZone($event, false)"
            @click.stop
          >
            <v-list-item-title
              class="d-flex justify-space-between align-center"
            >
              {{ child.name }}
              <div>
                <v-btn
                  class="mr-9"
                  variant="text"
                  @click.stop="
                    $emit('getEnrollments', {
                      enrollment: child.name,
                      parentOrg: organization,
                    })
                  "
                >
                  {{ child.enrollments }}
                  <v-icon end> mdi-account-multiple </v-icon>
                </v-btn>
                <v-menu :close-on-content-click="false">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      class="ml-2 mr-5"
                      density="comfortable"
                      icon="mdi-dots-vertical"
                      variant="text"
                      @click.stop
                    />
                  </template>
                  <v-list density="compact">
                    <v-list-item @click="confirmDelete(child)">
                      <v-list-item-title>Delete team</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
            </v-list-item-title>
          </v-list-item>
        </v-list-group>
        <v-list-item
          v-else
          draggable="true"
          @dragstart="($event) => startDrag(organization, team, $event)"
          @drop.stop="onDrop($event, team)"
          @dragover.prevent="isDropZone($event, true)"
          @dragenter.prevent="isDropZone($event, true)"
          @dragleave.prevent="isDropZone($event, false)"
        >
          <v-list-item-title class="d-flex justify-space-between align-center">
            {{ team.name }}
            <div>
              <v-btn
                class="mr-9"
                variant="text"
                @click.stop="
                  $emit('getEnrollments', {
                    enrollment: team.name,
                    parentOrg: organization,
                  })
                "
              >
                {{ team.enrollments }}
                <v-icon end> mdi-account-multiple </v-icon>
              </v-btn>
              <v-menu :close-on-content-click="false">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    class="ml-2 mr-5"
                    density="comfortable"
                    icon="mdi-dots-vertical"
                    variant="text"
                    @click.stop
                  />
                </template>
                <v-list density="compact">
                  <v-menu v-model="menu" :close-on-content-click="false">
                    <template v-slot:activator="{ props }">
                      <v-list-item v-bind="props">
                        <v-list-item-title>Add a team</v-list-item-title>
                      </v-list-item>
                    </template>
                    <v-card min-width="200">
                      <v-card-text>
                        <v-text-field
                          v-model="newTeam"
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
                            menu = false;
                            newTeam = '';
                          "
                        >
                          Cancel
                        </v-btn>
                        <v-btn @click="createTeam(team)"> Save </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-menu>
                  <v-list-item @click="confirmDelete(team)">
                    <v-list-item-title>Delete team</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </v-list-item-title>
        </v-list-item>
      </div>
    </v-list>
    <v-dialog v-model="dialog.isOpen" v-if="dialog.isOpen" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p class="pt-2 pb-2 text-body-2">{{ dialog.text }}</p>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog"> Cancel </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog"> OK </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </td>
</template>

<script>
export default {
  name: "ExpandedOrganization",
  props: {
    domains: {
      type: Array,
      required: false,
    },
    organization: {
      type: String,
      required: true,
    },
    addTeam: {
      type: Function,
      required: true,
    },
    deleteTeam: {
      type: Function,
      required: true,
    },
    fetchTeams: {
      type: Function,
      required: true,
    },
    isGroup: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      teams: [],
      openTeams: [],
      newTeam: "",
      dialog: {
        isOpen: false,
        title: "",
      },
      menu: false,
    };
  },
  methods: {
    async getTeams(parent) {
      const response = await this.fetchTeams({
        organization: this.organization,
        parent: parent,
      });

      const teams = response.data.teams.entities.map((team) => {
        return {
          name: team.name,
          enrollments: this.getEnrolledIndividuals(team.enrollments),
          children: team.numchild > 0 ? [] : undefined,
        };
      });

      return teams;
    },
    getEnrolledIndividuals(enrollments) {
      if (!enrollments) {
        return 0;
      }
      const uniqueIndividuals = new Set(
        enrollments.map((item) => item.individual?.mk)
      );

      return uniqueIndividuals.size;
    },
    async loadChildren(parent) {
      parent.children = await this.getTeams(parent.name);
    },
    async reloadTeams() {
      const openTeams = this.openTeams;
      this.teams = await this.getTeams();
      openTeams.forEach((openTeam) => {
        const updateTeam = this.teams.find(
          (team) => team.name === openTeam.name
        );
        if (updateTeam) {
          this.loadChildren(updateTeam);
        }
      });
    },
    startDrag(organization, item, event) {
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.setData("group", item.name);
      event.dataTransfer.setData("parentorg", organization);
    },
    async createTeam(parent) {
      try {
        const response = await this.addTeam(
          this.newTeam,
          this.organization,
          parent.name
        );
        if (!response.errors) {
          parent.children = parent.children || [];
          parent.children.push({
            name: this.newTeam,
            enrollments: 0,
            children: undefined,
          });
          this.newTeam = "";
          this.menu = false;
        }
      } catch (error) {
        Object.assign(this.dialog, {
          isOpen: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error creating team: ${error}`);
      }
    },
    async removeTeam(team) {
      try {
        const response = await this.deleteTeam(team.name, this.organization);
        if (!response.errors) {
          this.$logger.debug(`Deleted team ${team.name}`);
          this.removeTeamNode(team.name);
          this.closeDialog();
        }
      } catch (error) {
        Object.assign(this.dialog, {
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error deleting team ${team.name}: ${error}`);
      }
    },
    removeTeamNode(name, teams = this.teams) {
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
    confirmDelete(item) {
      Object.assign(this.dialog, {
        isOpen: true,
        title: `Delete ${item.name}?`,
        action: () => this.removeTeam(item),
      });
    },
    closeDialog() {
      Object.assign(this.dialog, {
        isOpen: false,
        title: "",
        text: "",
        action: null,
      });
    },
    isDropZone(event, isDragging) {
      const treeNode = event.target.closest(".v-list-item");
      const type = event.dataTransfer.getData("type");
      const types = event.dataTransfer.types;

      if (
        isDragging &&
        (type === "individuals" || types.includes("individuals"))
      ) {
        treeNode.classList.add("dropzone");
      } else {
        treeNode.classList.remove("dropzone");
      }
    },
    onDrop(event, item) {
      const types = event.dataTransfer.types;

      event.target.closest(".v-list-item").classList.remove("dropzone");

      if (types.includes("individuals")) {
        const droppedIndividuals = JSON.parse(
          event.dataTransfer.getData("individuals")
        ).filter((individual) => !individual.isLocked);
        if (droppedIndividuals.length > 0) {
          this.$emit("enroll", {
            individuals: droppedIndividuals,
            parentOrg: this.organization,
            group: item.name,
          });
        }
      }
    },
  },
  async created() {
    this.teams = await this.getTeams();
  },
};
</script>
<style lang="scss" scoped>
:deep(.v-treeview-node__toggle),
:deep(.v-treeview-node__level) {
  font-size: 1rem;
  width: 1rem;
}

.v-list-item[draggable="true"] {
  padding-left: 16px;
  &::before {
    font: normal normal normal 24px/1 "Material Design Icons";
    font-size: 1rem;
    content: "\F01DD";
    position: absolute;
    left: 0;
    top: 30%;
    opacity: 0;
    cursor: grab;
    color: rgba(0, 0, 0, 0.62);
  }

  &:hover {
    &::before {
      opacity: 1;
    }
  }
}

:deep(.v-list-item__append) > .v-icon ~ .v-list-item__spacer {
  width: 0;
}
</style>
