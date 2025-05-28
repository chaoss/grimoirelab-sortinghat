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
          createdAt: "2025-05-26T14:09:47.641485+00:00",
          name: "enroll",
          operations: [
            {
              args: { group: "Hogwarts" },
            },
          ],
        },
        {
          authoredBy: null,
          createdAt: "2025-05-21T14:07:57.895366+00:00",
          name: "merge-f95eb11f-974a-40b1-91bc-bb4060d5830a",
          operations: [
            {
              entityType: "identity",
              args: { identity: "4263b9a4f2e2cf5d2ec47f23ae4bec30d2e2d978" },
            },
          ],
        },
        {
          authoredBy: "username",
          createdAt: "2024-07-29T13:52:05.116020+00:00",
          name: "unmerge_identities",
        },
      ],
    },
  },
});
