<template>
  <v-dialog v-model="isOpen" persistent max-width="1000px">
    <v-card class="section">
      <v-card-title class="header">
        <span class="title"> {{ organization }} teams </span>
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
          >
            <template v-slot:append="{ item }">
              <v-row class="align-center">
                <v-edit-dialog @save="add(item)">
                  <v-icon>
                    mdi-plus-circle-outline
                  </v-icon>
                  <template v-slot:input>
                    <v-text-field
                      v-model="teamName"
                      label="Add a new team"
                      maxlength="50"
                      single-line
                    />
                  </template>
                </v-edit-dialog>
                <v-btn icon @click="confirmDelete(item)">
                  <v-icon>
                    mdi-delete
                  </v-icon>
                </v-btn>
              </v-row>
            </template>
          </v-treeview>
        </v-card-text>
        <v-card-actions>
          <v-row>
            <v-col cols="3">
              <v-edit-dialog @save="add()">
                <v-btn text small left outlined color="primary">
                  <v-icon small color="primary">mdi-plus-circle-outline</v-icon>
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
            </v-col>
          </v-row>
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
    organization: {
      type: String,
      required: false,
      default: null
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
      filters: { organization: this.organization },
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
      let filters = this.filters;
      filters["parent"] = item.name;
      item.children = [];
      const data = await this.getTeams(filters).then(result =>
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
        const response = await this.deleteTeam(item.name, this.organization);
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
        const response = await this.addTeam(
          this.teamName,
          this.organization,
          parent?.name
        );
        if (response) {
          if (parent) {
            await this.getSubTeams(parent);
          } else {
            this.teams.push({ name: this.teamName, children: undefined });
          }
          this.teamName = "";
          this.$logger.debug(`Added team ${this.teamName}`);
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
