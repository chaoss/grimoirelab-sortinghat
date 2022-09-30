import JobModal from "./JobModal.vue";

export default {
  title: "JobModal",
  excludeStories: /.*Data$/
};

const JobModalTemplate = `
  <div class="ma-auto">
    <v-btn color="primary" dark @click.stop="open = true">
      Open Dialog
    </v-btn>
    <job-modal :is-open.sync="open"/>
  </div>`;

export const Default = () => ({
  components: { JobModal },
  template: JobModalTemplate,
  data: () => ({
    open: false
  })
});
