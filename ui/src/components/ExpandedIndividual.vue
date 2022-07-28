<template>
  <td :class="{ compact: compact }" colspan="4">
    <v-subheader v-if="!compact">Profile</v-subheader>
    <v-row v-if="!compact" class="indented mb-2 mt">
      <div class="ml-4">
        <span class="grey--text text--darken-2">Gender: </span>
        <span v-if="isLocked">{{ gender || " -" }}</span>
        <v-edit-dialog v-else @save="$emit('edit', { gender: form.gender })">
          {{ gender || " -" }}
          <v-icon small right>
            mdi-lead-pencil
          </v-icon>
          <template v-slot:input>
            <v-text-field
              v-model="form.gender"
              label="Edit gender"
              maxlength="30"
              single-line
            ></v-text-field>
          </template>
        </v-edit-dialog>
      </div>
      <div class="ml-6">
        <span class="grey--text text--darken-2">Country: </span>
        <span v-if="isLocked">{{ country ? country.name : "-" }}</span>
        <v-edit-dialog
          v-else
          @close="
            $emit('edit', {
              countryCode: form.country ? form.country.code : ''
            })
          "
        >
          <span class="black--text">{{ country ? country.name : "-" }}</span>
          <v-icon small right>
            mdi-lead-pencil
          </v-icon>
          <template v-slot:input>
            <v-combobox
              v-model="form.country"
              :items="countries"
              label="Country"
              item-text="name"
              @click.once="getCountryList"
            />
          </template>
        </v-edit-dialog>
      </div>
    </v-row>
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
      @openEnrollmentModal="$emit('openEnrollmentModal', uuid)"
      @openTeamModal="$emit('openTeamModal', { uuid, organization: $event })"
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
    EnrollmentList
  },
  props: {
    gender: {
      type: String,
      required: false
    },
    country: {
      type: Object,
      required: false
    },
    isBot: {
      type: Boolean,
      required: false
    },
    isLocked: {
      type: Boolean,
      required: false
    },
    identities: {
      type: Array,
      required: true
    },
    enrollments: {
      type: Array,
      required: true
    },
    compact: {
      type: Boolean,
      required: false,
      default: false
    },
    uuid: {
      type: String,
      required: true
    },
    getCountries: {
      type: Function,
      required: false
    }
  },
  data() {
    return {
      countries: [],
      form: {
        gender: this.gender,
        country: this.country,
        isBot: this.isBot
      },
      enrollmentsForm: []
    };
  },
  methods: {
    async getCountryList() {
      const response = await this.getCountries();
      if (response) {
        this.countries = response;
      }
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.indented {
  margin-left: 40px;
  background-color: transparent;
}

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

  ::v-deep .uuid {
    display: none;
  }

  ::v-deep .indented {
    padding: 0;
    margin: 0;
    text-align: center;
  }

  .row-border:not(:last-child) {
    border: 0;
  }
}

.v-small-dialog__activator {
  .v-icon {
    opacity: 0;
    padding-bottom: 2px;
  }

  &:hover {
    .v-icon {
      opacity: 1;
    }
  }
}
.v-small-dialog,
::v-deep .v-small-dialog__activator {
  display: inline-block;
}
</style>
