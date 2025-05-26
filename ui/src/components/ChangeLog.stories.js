import ChangeLog from "./ChangeLog.vue";

export default {
  title: "ChangeLog",
  excludeStories: /.*Data$/,
};

const template = '<change-log :changes="items" />';

export const Default = () => ({
  components: { ChangeLog },
  template: template,
  props: {
    items: {
      default: [
        {
          authoredBy: "username",
          createdAt:"2025-05-26T14:09:47.641485+00:00",
          name: "enroll"
        },
        {
          authoredBy: null,
          createdAt: "2025-05-21T14:07:57.895366+00:00",
          name: "merge-f95eb11f-974a-40b1-91bc-bb4060d5830a"
        },
        {
          authoredBy: "username",
          createdAt: "2024-07-29T13:52:05.116020+00:00",
          name: "unmerge_identities"
        }
      ]
    }
  },
});
