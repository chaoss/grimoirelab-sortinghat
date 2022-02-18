import TeamEnrollModal from "./TeamEnrollModal.vue";

export default {
  title: "TeamEnrollModal",
  excludeStories: /.*Data$/
};

const template = `<team-enroll-modal
    :is-open='isOpen'
    :organization='organization'
    :enroll='enroll'
    uuid="123"
  />`;

export const Default = () => ({
  components: { TeamEnrollModal },
  template: template,
  data: () => ({
    isOpen: true,
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
    isOpen: true,
    organization: "Hogwarts"
  }),
  methods: {
    enroll() {
      throw "Example error";
    }
  }
});
