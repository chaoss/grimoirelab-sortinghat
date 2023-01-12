import { formatIndividuals } from "../utils/actions";

const enrollMixin = {
  data() {
    return {
      enrollmentModal: {
        open: false,
        title: "",
        text: "",
        action: "",
        organization: null,
        uuid: null,
      },
    };
  },
  methods: {
    confirmEnroll(uuid, group) {
      Object.assign(this.enrollmentModal, {
        open: true,
        title: `Affiliate individual to ${
          group ? group + "?" : "an organization"
        }`,
        organization: group,
        uuid: uuid,
        text: null,
        dateFrom: null,
        dateTo: null,
        showDates: true,
        action: () => this.enrollIndividual(),
      });
    },
    async enrollIndividual(uuid, group, dateFrom, dateTo) {
      this.closeDialog();
      const response = await this.enroll(uuid, group, dateFrom, dateTo);
      if (response) {
        this.$emit("updateWorkspace", {
          update: formatIndividuals([response.data.enroll.individual]),
        });
        this.$emit("updateOrganizations");
        this.$emit("updateIndividuals");
        if (this.queryIndividuals) {
          this.queryIndividuals();
        }
        if (this.individual) {
          this.individual = formatIndividuals([
            response.data.enroll.individual,
          ])[0];
        }
        this.$logger.debug("Enrolled individual", {
          group,
          uuid,
          dateFrom,
          dateTo,
        });
      }
    },
  },
};

export { enrollMixin };
