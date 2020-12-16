import { formatIndividuals } from "../utils/actions";

const enrollMixin = {
  methods: {
    confirmEnroll(uuid, organization) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate individual to ${organization}?`,
        text: "",
        action: () => this.enrollIndividual(uuid, organization)
      });
    },
    async enrollIndividual(uuid, organization) {
      this.dialog.open = false;
      try {
        const response = await this.enroll(uuid, organization);
        if (response) {
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.enroll.individual])
          });
          this.$emit("updateOrganizations");
          this.$emit("updateIndividuals");
          if (this.queryIndividuals) {
            this.queryIndividuals();
          }
        }
      } catch (error) {
        Object.assign(this.snackbar, { open: true, text: error });
      }
    }
  }
};

export { enrollMixin };
