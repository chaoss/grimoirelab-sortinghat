import TeamModal from "./TeamModal.vue";

export default {
  title: "TeamModal",
  excludeStories: /.*Data$/,
};

const TeamModalTemplate = `  <div class="ma-auto">
    <v-btn color="primary" dark @click.stop="modal.open = true">
      Open Dialog
    </v-btn><team-modal :is-open.sync="modal.open" :parent="organization"  :add-team="addTeam" :delete-team="deleteTeam" :fetch-teams="fetchTeams"/></div>`;

export const Default = () => ({
  components: { TeamModal },
  template: TeamModalTemplate,
  data: () => ({
    organization: "Ministry of Magic",
    modal: {
      open: false,
    },
    query: [
      {
        data: {
          teams: {
            entities: [
              {
                name: "Committee on Experimental Charms",
                numchild: 0,
              },
              {
                name: "Department of Magical Law Enforcement",
                numchild: 2,
              },
              {
                name: "Department of Magical Accidents and Catastrophes",
                numchild: 0,
              },
              {
                name: "Department for the Regulation and Control of Magical Creatures",
                numchild: 1,
              },
              {
                name: "Auror Office",
                parent: "Department of Magical Law Enforcement",
                numchild: 1,
              },
              {
                name: "Calamity Investigators",
                parent: "Auror Office",
                numchild: 0,
              },
              {
                name: "Improper Use of Magic Office",
                parent: "Department of Magical Law Enforcement",
                numchild: 0,
              },
              {
                name: "Beast Division",
                parent:
                  "Department for the Regulation and Control of Magical Creatures",
                numchild: 0,
              },
            ],
          },
        },
      },
    ],
  }),
  methods: {
    fetchTeams(filters) {
      let data = [];
      if (Object.keys(filters).includes("parent")) {
        this.query[0].data.teams.entities.forEach((team) => {
          if (team["parent"] === filters["parent"]) {
            data.push(team);
          }
        });
      } else {
        this.query[0].data.teams.entities.forEach((team) => {
          if (team["parent"] === undefined) {
            data.push(team);
          }
        });
      }
      const resp = {
        data: {
          teams: {
            entities: data,
          },
        },
      };

      return resp;
    },
    addTeam(team, organization, parent) {
      const insertData = {
        name: team,
      };
      if (parent) {
        insertData["parent"] = parent;
      }
      this.query[0].data.teams.entities.push(insertData);
      return true;
    },
    deleteTeam(team, organization) {
      this.query[0].data.teams.entities =
        this.query[0].data.teams.entities.filter((elem) => elem.name != team);
      return true;
    },
  },
});
