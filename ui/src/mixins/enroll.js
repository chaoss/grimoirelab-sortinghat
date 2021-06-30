import { formatIndividuals } from "../utils/actions";
import DateInput from "../components/DateInput.vue";

const enrollMixin = {
  components: { DateInput },
  methods: {
    confirmEnroll(uuid, organization) {
      Object.assign(this.dialog, {
        open: true,
        title: `Affiliate individual to ${organization}?`,
        text: null,
        dateFrom: null,
        dateTo: null,
        showDates: true,
        action: () =>
          this.enrollIndividual(
            uuid,
            organization,
            this.dialog.dateFrom,
            this.dialog.dateTo
          )
      });
    },
    async enrollIndividual(uuid, organization, dateFrom, dateTo) {
      this.closeDialog();
      try {
        const response = await this.enroll(
          uuid,
          organization,
          dateFrom,
          dateTo
        );
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
            organization,
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
