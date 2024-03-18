import MatchesModal from "./MatchesModal.vue";

export default {
  title: "MatchesModal",
  excludeStories: /.*Data$/,
};

const template = `
  <div data-app="true" class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open modal
    </v-btn>
    <matches-modal
      :is-open.sync="isOpen"
      :recommend-matches="recommendMatches"
      uuid="abc123"
    />
  </div>
`;

export const Default = () => ({
  components: { MatchesModal },
  template: template,
  data: () => ({
    isOpen: false,
  }),
  methods: {
    recommendMatches() {
      return {
        data: {
          recommendMatches: {
            jobId: "b65d2170-a560-4b20-954e-fc8c9f5afdd4",
          },
        },
      };
    },
  },
});

export const Error = () => ({
  components: { MatchesModal },
  template: template,
  data: () => ({
    isOpen: false,
  }),
  methods: {
    recommendMatches() {
      throw new TypeError("Error creating job");
    },
  },
});
