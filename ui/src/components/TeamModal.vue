<template>
  <v-dialog v-if="isOpen" v-model="isOpen" persistent max-width="550px">
    <v-card class="section">
      <v-card-title class="header">
        <span class="title"> {{ parent }} teams </span>
      </v-card-title>
      <form>
        <v-card-text class="team-modal-content">
          <v-treeview
            :items="teams"
            :load-children="getSubTeams"
            :open.sync="open"
            color="warning"
            open-on-click
            transition
            dense
          >
            <template v-slot:append="{ item }">
              <v-row class="align-center">
                <v-edit-dialog @save="add(item)">
                  <v-btn aria-label="Add team" icon>
                    <v-icon small>
                      mdi-plus-circle-outline
                    </v-icon>
                  </v-btn>
                  <template v-slot:input>
                    <v-text-field
                      v-model="teamName"
                      label="Add a new team"
                      maxlength="50"
                      single-line
                    />
                  </template>
                </v-edit-dialog>
                <v-btn
                  aria-label="Delete team"
                  icon
                  @click="confirmDelete(item)"
                >
                  <v-icon small>
                    mdi-delete
                  </v-icon>
                </v-btn>
              </v-row>
            </template>
          </v-treeview>
        </v-card-text>
        <v-card-actions>
          <v-edit-dialog @save="add()">
            <v-btn text small left outlined color="primary" class="ml-4">
              <v-icon small left color="primary"
                >mdi-plus-circle-outline</v-icon
              >
              Add team
            </v-btn>
            <template v-slot:input>
              <v-text-field
                v-model="teamName"
                label="Add a new team"
                maxlength="50"
                single-line
              />
            </template>
          </v-edit-dialog>
          <v-spacer></v-spacer>
          <v-btn color="primary darken-1" text @click.prevent="closeModal">
            Close
          </v-btn>
        </v-card-actions>
      </form>
    </v-card>
    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p class="pt-2 pb-2 text-body-2">{{ dialog.text }}</p>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">
            Cancel
          </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>
<script>
export default {
  name: "TeamModal",
  props: {
    isOpen: {
      type: Boolean,
      required: false,
      default: false
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
    parent: {
      type: String,
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
      filters: {},
      teams: [],
      open: [],
      teamName: "",
      dialog: {
        open: false,
        title: "",
        text: "",
        action: ""
      }
    };
  },
  methods: {
    closeModal() {
      this.errorMessage = "";
      this.$emit("updateTeams");
      this.$emit("update:isOpen", false);
    },
    async getSubTeams(item) {
      Object.assign(this.filters, { parent: item.name });
      item.children = [];
      const data = await this.getTeams(this.filters).then(result =>
        result.forEach(team =>
          item.children.push({
            name: team.name,
            children: team.numchild > 0 ? [] : undefined
          })
        )
      );
      return data;
    },
    closeDialog() {
      Object.assign(this.dialog, {
        open: false,
        title: "",
        text: "",
        action: ""
      });
    },
    async getTeams(filters = this.filters) {
      const response = await this.fetchTeams(filters);
      return response.data.teams.entities;
    },
    confirmDelete(item) {
      Object.assign(this.dialog, {
        open: true,
        title: "Delete this team?",
        text: item.name,
        action: () => this.delete(item)
      });
    },
    findAndDelete(name, items = null, found = false) {
      if (!found) {
        if (!items) {
          items = this.teams;
        }
        items.forEach((child, index) => {
          if (child.name == name) {
            items.splice(index, 1);
            found = true;
          }
          if (child.children) {
            this.findAndDelete(name, child.children);
          }
        });
      }
    },
    async delete(item) {
      this.closeDialog();
      try {
        const organization = this.isGroup ? null : this.parent;
        const response = await this.deleteTeam(item.name, organization);
        if (response) {
          this.findAndDelete(item.name);
          this.$logger.debug(`Deleted team ${item.name}`);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(`Error deleting team ${item.name}: ${error}`);
      }
    },
    async add(parent = null) {
      this.closeDialog();
      try {
        const organization = this.isGroup ? null : this.parent;
        let team;
        if (parent) {
          team = parent.name;
        } else {
          team = this.isGroup ? this.parent : null;
        }
        const response = await this.addTeam(this.teamName, organization, team);
        if (response) {
          if (parent) {
            await this.getSubTeams(parent);
          } else {
            this.teams.push({ name: this.teamName, children: undefined });
          }
          this.$logger.debug(`Added team ${this.teamName}`);
          this.teamName = "";
          return response;
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.teamName = "";
        this.$logger.error(`Error adding team ${this.teamName}: ${error}`);
      }
    }
  },
  async created() {
    if (this.isGroup) {
      this.filters = { parent: this.parent };
    } else {
      this.filters = { organization: this.parent };
    }
    const teamObjects = await this.getTeams();
    teamObjects.forEach(team =>
      this.teams.push({
        name: team.name,
        children: team.numchild > 0 ? [] : undefined
      })
    );
  }
};
</script>
