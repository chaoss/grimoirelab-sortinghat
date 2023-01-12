import EnrollModal from "./EnrollModal.vue";

export default {
  title: "EnrollModal",
  excludeStories: /.*Data$/,
};

const template = `
  <div data-app="true" class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Dialog
    </v-btn>
    <enroll-modal
      :is-open.sync='isOpen'
      :organization='organization'
      :enroll='enroll'
      :title='title'
      uuid="123"
    />
  </div>
`;

export const Default = () => ({
  components: { EnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: null,
    title: "Enroll individual to an organization",
  }),
  methods: {
    enroll() {
      return true;
    },
  },
});

export const WithOrganization = () => ({
  components: { EnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: "Hogwarts",
    title: "Enroll individual to Hogwarts?",
  }),
  methods: {
    enroll() {
      return true;
    },
  },
});
