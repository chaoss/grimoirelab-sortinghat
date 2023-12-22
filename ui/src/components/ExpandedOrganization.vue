<template>
  <td colspan="3" class="pa-2">
    <v-treeview
      :items="teams"
      :load-children="loadChildren"
      :open.sync="openTeams"
      expand-icon="mdi-chevron-down"
      dense
      open-on-click
      return-object
    >
      <template v-slot:label="{ item }">
        <v-row
          draggable="true"
          class="align-center"
          @dragstart="($event) => startDrag(organization, item, $event)"
          @drop.stop="onDrop($event, item)"
          @dragover.prevent="isDropZone($event, true)"
          @dragenter.prevent="isDropZone($event, true)"
          @dragleave.prevent="isDropZone($event, false)"
        >
          <v-col>
            <span class="font-weight-medium">{{ item.name }}</span>
          </v-col>
          <v-col class="d-flex justify-end mr-7">
            <v-btn
              small
              depressed
              color="transparent"
              @click.stop="
                $emit('getEnrollments', {
                  enrollment: item.name,
                  parentOrg: organization,
                })
              "
            >
              {{ item.enrollments }}
              <v-icon small right> mdi-account-multiple </v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </template>
      <template v-slot:append="{ item }">
        <v-menu left nudge-left="16">
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon small v-bind="attrs" v-on="on" class="mr-9">
              <v-icon small>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-list dense>
            <v-edit-dialog
              large
              @save="createTeam(item)"
              @cancel="newTeam = ''"
            >
              <v-list-item>
                <v-list-item-title>Add a team</v-list-item-title>
              </v-list-item>
              <template v-slot:input>
                <h6 class="text-subtitle-2 mt-2">
                  Add team to {{ item.name }}
                </h6>
                <v-text-field
                  v-model="newTeam"
                  label="Name"
                  maxlength="50"
                  single-line
                />
              </template>
            </v-edit-dialog>
            <v-list-item @click="confirmDelete(item)">
              <v-list-item-title>Delete team</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-treeview>
    <p class="ma-3 text--secondary ml-9" v-if="teams.length === 0">No teams</p>
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
        enrollments.map((item) => item.id)
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
      const treeNode = event.target.closest(".v-treeview-node__root");
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

      event.target
        .closest(".v-treeview-node__root")
        .classList.remove("dropzone");

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
::v-deep .v-treeview-node__toggle,
::v-deep .v-treeview-node__level {
  font-size: 1rem;
  width: 1rem;
}

.row[draggable="true"] {
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
</style>
