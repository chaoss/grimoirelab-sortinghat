import TeamEnrollModal from "./TeamEnrollModal.vue";

export default {
  title: "TeamEnrollModal",
  excludeStories: /.*Data$/,
};

const template = `
  <div data-app="true" class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Dialog
    </v-btn>
    <team-enroll-modal
      :is-open.sync='isOpen'
      :organization='organization'
      :team="team"
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
    organization: "Hogwarts",
    team: null,
  }),
  methods: {
    enroll() {
      return {
        data: {
          enroll: {},
        },
      };
    },
  },
});

export const WithTeam = () => ({
  components: { TeamEnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: "Hogwarts",
    team: "Griffindor",
  }),
  methods: {
    enroll() {
      return {
        data: {
          enroll: {},
        },
      };
    },
  },
});

export const ErrorOnSave = () => ({
  components: { TeamEnrollModal },
  template: template,
  data: () => ({
    isOpen: false,
    organization: "Hogwarts",
    team: null,
  }),
  methods: {
    enroll() {
      throw new Error("Example error");
    },
  },
});
