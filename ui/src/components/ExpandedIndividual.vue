<template>
  <td :class="{ compact: compact }" colspan="5">
    <identities-list
      :identities="identities"
      :uuid="uuid"
      :compact="compact"
      :is-locked="isLocked"
      draggable
      @unmerge="$emit('unmerge', $event)"
    />

    <enrollment-list
      :enrollments="enrollments"
      :compact="compact"
      :is-locked="isLocked"
      @openEnrollmentModal="$emit('openEnrollmentModal')"
      @openTeamModal="
        $emit('openTeamModal', { uuid, organization: $event, enrollments })
      "
      @updateEnrollment="
        $emit('updateEnrollment', Object.assign($event, { uuid: uuid }))
      "
      @withdraw="$emit('withdraw', $event)"
    />
  </td>
</template>

<script>
import IdentitiesList from "./IdentitiesList.vue";
import EnrollmentList from "./EnrollmentList.vue";

export default {
  name: "ExpandedIndividual",
  components: {
    IdentitiesList,
    EnrollmentList,
  },
  props: {
    gender: {
      type: String,
      required: false,
    },
    country: {
      type: Object,
      required: false,
    },
    isBot: {
      type: Boolean,
      required: false,
    },
    isLocked: {
      type: Boolean,
      required: false,
    },
    identities: {
      type: Array,
      required: true,
    },
    enrollments: {
      type: Array,
      required: true,
    },
    compact: {
      type: Boolean,
      required: false,
      default: false,
    },
    uuid: {
      type: String,
      required: true,
    },
    getCountries: {
      type: Function,
      required: false,
    },
  },
  data() {
    return {
      countries: [],
      form: {
        gender: this.gender,
        country: this.country,
        isBot: this.isBot,
      },
      enrollmentsForm: [],
    };
  },
  methods: {
    async getCountryList() {
      const response = await this.getCountries();
      if (response) {
        this.countries = response;
      }
    },
  },
};
</script>
<style lang="scss" scoped>
@use "../styles/index.scss";

.compact {
  border-bottom: 0;
  background-color: #ffffff;
  font-size: 0.9rem;
  line-height: 1rem;
  padding: 0.5rem;

  .v-list-item__content,
  .v-sheet--tile {
    padding: 0;
  }

  :deep(.uuid) {
    display: none;
  }

  :deep(.indented) {
    padding: 0;
    margin: 0;
    text-align: center;
  }

  .row-border:not(:last-child) {
    border: 0;
  }
}

.v-small-dialog,
:deep(.v-small-dialog__activator) {
  display: inline-block;
}
</style>
