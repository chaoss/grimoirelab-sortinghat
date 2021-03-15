import ProfileModal from "./ProfileModal.vue";

export default {
  title: "ProfileModal",
  excludeStories: /.*Data$/
};

const ProfileModalTemplate = `
  <div class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Dialog
    </v-btn>
    <profile-modal
      :is-open.sync="isOpen"
      :add-identity="mockFunction"
      :update-profile="mockFunction"
      :enroll="mockFunction"
      :get-countries="getCountries.bind(this)"
    />
  </div>
`;

export const Default = () => ({
  components: { ProfileModal },
  template: ProfileModalTemplate,
  data: () => ({
    isOpen: false,
    countries: [
      { code: "AD", name: "Andorra" },
      { code: "AE", name: "United Arab Emirates" },
      { code: "AF", name: "Afghanistan" },
      { code: "AG", name: "Antigua and Barbuda" },
      { code: "AI", name: "Anguilla" },
      { code: "AL", name: "Albania" },
      { code: "AM", name: "Armenia" }
    ]
  }),
  methods: {
    mockFunction() {
      return true;
    },
    getCountries() {
      return this.countries;
    }
  }
});
