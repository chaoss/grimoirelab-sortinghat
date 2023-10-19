import { formatIndividuals } from "../utils/actions";
import { addOrganization } from "../apollo/mutations";

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
      teamModal: {
        isOpen: false,
        organization: null,
        team: null,
        uuid: null,
        enrollments: null,
      },
    };
  },
  methods: {
    confirmEnroll(individual, event = {}) {
      const { group, parentOrg } = event;
      if (parentOrg) {
        Object.assign(this.teamModal, {
          isOpen: true,
          organization: parentOrg,
          team: group,
          uuid: individual.uuid,
          enrollments: individual.enrollments,
        });
      } else {
        Object.assign(this.enrollmentModal, {
          open: true,
          title: `Affiliate individual to ${
            group ? group + "?" : "an organization"
          }`,
          organization: group,
          uuid: individual.uuid,
          text: null,
          dateFrom: null,
          dateTo: null,
          showDates: true,
          action: () => this.enrollIndividual(),
        });
      }
    },
    async enrollIndividual(uuid, group, dateFrom, dateTo, parentOrg) {
      this.closeDialog();
      const response = await this.enroll(
        uuid,
        group,
        dateFrom,
        dateTo,
        parentOrg
      );
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
          parentOrg,
        });
        Object.assign(this.teamModal, {
          isOpen: false,
          organization: null,
          team: null,
          uuid: null,
        });
      }
    },
    async addOrganization(name) {
      const response = await addOrganization(this.$apollo, name);
      return response;
    },
  },
};

export { enrollMixin };
