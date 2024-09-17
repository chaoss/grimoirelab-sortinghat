import GenericModal from "./GenericModal.vue";

export default {
  title: "GenericModal",
  excludeStories: /.*Data$/,
};

const template = `
  <div data-app="true" class="ma-auto">
    <v-btn color="primary" dark @click.stop="isOpen = true">
      Open Modal
    </v-btn>
    <generic-modal
      v-model:is-open='isOpen'
      :title
      :text
      :action
      :actionButtonLabel
      :actionButtonColor
      :dismissButtonLabel
    />
  </div>
`;

export const Default = () => ({
  components: { GenericModal },
  template: template,
  data: () => ({
    isOpen: false,
    title: "Modal title",
    text: `Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
      eiusmod tempor incididunt ut labore et dolore magna aliqua.`,
    action: null,
    actionButtonLabel: null,
    actionButtonColor: null,
    dismissButtonLabel: "Close",
  }),
});

export const DestructiveAction = () => ({
  components: { GenericModal },
  template: template,
  data: () => ({
    isOpen: false,
    title: "Delete item?",
    text: null,
    action: () => {},
    actionButtonLabel: "Delete",
    actionButtonColor: "error",
    dismissButtonLabel: "Cancel",
  }),
});
