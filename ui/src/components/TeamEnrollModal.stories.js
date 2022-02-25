import TeamEnrollModal from "./TeamEnrollModal.vue";

export default {
  title: "TeamEnrollModal",
  excludeStories: /.*Data$/
};

const template = `
  <div data-app="true" class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Dialog
    </v-btn>
    <team-enroll-modal
      :is-open.sync='isOpen'
      :organization='organization'
      :enroll='enroll'
      uuid="123"
    />
  </div>
`;

export const Default = () => ({
  components: { TeamEnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: "Hogwarts"
  }),
  methods: {
    enroll() {
      return true;
    }
  }
});

export const ErrorOnSave = () => ({
  components: { TeamEnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: "Hogwarts"
  }),
  methods: {
    enroll() {
      throw "Example error";
    }
  }
});
