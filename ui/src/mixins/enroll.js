import { formatIndividuals } from "../utils/actions";
import DateInput from "../components/DateInput.vue";

const enrollMixin = {
  components: { DateInput },
  methods: {
    confirmEnroll(uuid, group) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate individual to ${group}?`,
        text: null,
        dateFrom: null,
        dateTo: null,
        showDates: true,
        action: () =>
          this.enrollIndividual(
            uuid,
            group,
            this.dialog.dateFrom,
            this.dialog.dateTo
          )
      });
    },
    async enrollIndividual(uuid, group, dateFrom, dateTo) {
      this.closeDialog();
      try {
        const response = await this.enroll(uuid, group, dateFrom, dateTo);
        if (response) {
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.enroll.individual])
          });
          this.$emit("updateOrganizations");
          this.$emit("updateIndividuals");
          if (this.queryIndividuals) {
            this.queryIndividuals();
          }
          this.$logger.debug("Enrolled individual", {
            group,
            uuid,
            dateFrom,
            dateTo
          });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
      }
    }
  }
};

export { enrollMixin };
