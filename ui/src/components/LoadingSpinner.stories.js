import LoadingSpinner from "./LoadingSpinner.vue";

export default {
  title: "LoadingSpinner",
  excludeStories: /.*Data$/,
};

const template = `<loading-spinner :label="label"/>`;

export const Default = () => ({
  components: { LoadingSpinner },
  template: template,
  data: () => ({
    label: null,
  }),
});

export const Label = () => ({
  components: { LoadingSpinner },
  template: template,
  data: () => ({
    label: "Loading...",
  }),
});
