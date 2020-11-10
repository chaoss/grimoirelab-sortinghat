import { storiesOf } from "@storybook/vue";

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
    />
  </div>
`;

export const Default = () => ({
  components: { ProfileModal },
  template: ProfileModalTemplate,
  data: () => ({
    isOpen: false
  }),
  methods: {
    mockFunction() {
      return true;
    }
  }
});
