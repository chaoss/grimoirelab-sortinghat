import ImporterModal from "./ImporterModal.vue";

export default {
  title: "ImporterModal",
  excludeStories: /.*Data$/,
};

const template = `
<div class="ma-auto">
  <v-btn color="primary" dark @click.stop="modal.isOpen = true">
    Open modal
  </v-btn>
  <importer-modal
    :is-open="modal.isOpen"
    :create-task="() => {}"
    :edit-task="() => {}"
    :task="modal.task"
    :importer="modal.importer"
  />
</div>
`;

export const Default = () => ({
  components: { ImporterModal },
  template: template,
  data: () => ({
    modal: {
      isOpen: false,
      task: {},
      importer: {
        args: ["url", "token"],
        name: "Backend",
      },
    },
  }),
});

export const EditTask = () => ({
  components: { ImporterModal },
  template: template,
  data: () => ({
    modal: {
      isOpen: false,
      task: {
        url: "http://test.com",
        interval: 45,
        id: 1,
      },
      importer: {
        args: ["url", "token"],
        name: "Backend",
      },
    },
  }),
});
