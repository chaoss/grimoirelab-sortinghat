import OrganizationModal from "./OrganizationModal.vue";

export default {
  title: "OrganizationModal",
  excludeStories: /.*Data$/
};

const OrganizationModalTemplate = `
  <div class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Dialog
    </v-btn>
    <organization-modal
      :is-open.sync="isOpen"
      :add-domain="addDomain"
      :add-organization="addDomain"
      :delete-domain="addDomain"                           l
    />
  </div>
`;

export const Default = () => ({
  components: { OrganizationModal },
  template: OrganizationModalTemplate,
  data: () => ({
    isOpen: false
  }),
  methods: {
    addDomain() {
      return true;
    }
  }
});

export const ErrorOnSave = () => ({
  components: { OrganizationModal },
  template: OrganizationModalTemplate,
  data: () => ({
    isOpen: false
  }),
  methods: {
    addDomain() {
      throw new Error("Example error");
    }
  }
});
