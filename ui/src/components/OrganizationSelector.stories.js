import OrganizationSelector from "./OrganizationSelector.vue";

export default {
  title: "OrganizationSelector",
  excludeStories: /.*Data$/,
};

const template = `
  <div class="ma-5 col-3">
    <organization-selector
      v-model="model"
      :fetch-organizations="fetchOrganizations"
      :add-organization="addOrganization"
    />
  </div>
`;

const organizations = {
  entities: [
    { name: "Hogwarts School of Witchcraft and Wizardry" },
    { name: "Advocates to the Wizarding World" },
    { name: "Agency for the Protection of Wizarding Secrecy" },
    { name: "Azkaban Security Officials" },
    { name: "British Wizard Duelling Association" },
    { name: "Celestial Ball decorating committee" },
    { name: "Enchanted Feather Co." },
    { name: "Dark Arts Civil Protection Council" },
    { name: "Dark Force Defence League" },
    { name: "East Coast Wizards" },
    { name: "Egyptian Owl Union" },
    { name: "French Magical Department" },
    { name: "Herbology High Commission" },
    { name: "Institute of Muggle Studies" },
    { name: "Potions Associations" },
    { name: "Salem Witches' Institute" },
  ],
};

export const Default = () => ({
  components: { OrganizationSelector },
  template: template,
  data: () => ({
    model: "",
    organizations: organizations,
  }),
  methods: {
    fetchOrganizations(page, items, filters) {
      const results = JSON.parse(JSON.stringify(this.organizations));
      if (filters.term) {
        results.entities = results.entities.filter((organization) =>
          organization.name.toUpperCase().includes(filters.term.toUpperCase())
        );
      }
      return results;
    },
    addOrganization(name) {
      return {
        data: {
          addOrganization: {
            organization: {
              name: name,
            },
          },
        },
      };
    },
  },
});

export const SelectedOrganization = () => ({
  components: { OrganizationSelector },
  template: template,
  data: () => ({
    model: "Institute of Muggle Studies",
    organizations: organizations,
  }),
  methods: {
    fetchOrganizations(page, items, filters) {
      const results = JSON.parse(JSON.stringify(this.organizations));
      if (filters.term) {
        results.entities = results.entities.filter((organization) =>
          organization.name.toUpperCase().includes(filters.term.toUpperCase())
        );
      }
      return results;
    },
    addOrganization(name) {
      return {
        data: {
          addOrganization: {
            organization: {
              name: name,
            },
          },
        },
      };
    },
  },
});
