<template>
  <div class="pb-2">
    <v-list-subheader class="mb-2">
      <span class="text-subtitle-2"> Organizations ({{ items.length }}) </span>
      <div v-if="!compact">
        <v-btn
          class="mr-4"
          size="small"
          variant="outlined"
          :disabled="isLocked"
          @click="$emit('openEnrollmentModal')"
        >
          <v-icon size="small" start>mdi-plus</v-icon>
          Add
        </v-btn>
        <v-btn
          size="small"
          variant="outlined"
          :disabled="enrollments.length < 1 || isLocked"
          @click="withdrawAll"
        >
          <v-icon size="small" start>mdi-delete</v-icon>
          Remove all
        </v-btn>
      </div>
    </v-list-subheader>
    <v-table v-if="compact" density="compact">
      <template v-slot:default>
        <thead v-if="enrollments.length > 0">
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">From</th>
            <th class="text-left">To</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="enrollment in enrollments" :key="enrollment.name">
            <td>{{ enrollment.group.name }}</td>
            <td>{{ formatDate(enrollment.start) }}</td>
            <td>{{ formatDate(enrollment.end) }}</td>
          </tr>
        </tbody>
      </template>
    </v-table>
    <v-row v-else v-for="item in items" :key="item.id" class="mx-2">
      <v-col cols="1" class="pl-2">
        <v-tooltip v-if="!item.group.parentOrg" location="bottom">
          <template v-slot:activator="{ props }">
            <v-icon v-bind="props" class="mr-3"> mdi-sitemap </v-icon>
          </template>
          <span>Organization</span>
        </v-tooltip>
        <v-tooltip v-else location="bottom">
          <template v-slot:activator="{ props }">
            <v-icon v-bind="props" class="mr-3"> mdi-account-multiple </v-icon>
          </template>
          <span>Team</span>
        </v-tooltip>
      </v-col>
      <v-col cols="2"> {{ item.group.name }} </v-col>
      <v-col cols="2">
        <v-menu
          v-model="item.form.fromDateMenu"
          :close-on-content-click="false"
          v-model:return-value="item.form.fromDate"
          transition="scale-transition"
          offset-y
          min-width="290px"
        >
          <template v-slot:activator="{ props }">
            <button
              :disabled="isLocked"
              v-bind="props"
              class="v-small-dialog__activator"
            >
              <span class="grey--text text--darken-2">
                {{ formatDate(item.start) }}
              </span>
              <v-icon size="small" end> mdi-lead-pencil </v-icon>
            </button>
          </template>
          <v-card min-width="180">
            <v-card-text>
              <date-input
                v-model="item.form.fromDate"
                label="Date from"
                nudge-top="20"
                nudge-right="10"
                :max="item.end"
              />
            </v-card-text>
            <v-card-actions class="pt-0">
              <v-spacer></v-spacer>
              <v-btn
                text
                color="primary"
                @click="item.form.fromDateMenu = false"
              >
                Cancel
              </v-btn>
              <v-btn
                :disabled="!item.form.fromDate"
                color="primary"
                text
                @click="
                  $emit('updateEnrollment', {
                    fromDate: item.start,
                    toDate: item.end,
                    newFromDate: item.form.fromDate,
                    group: item.group.name,
                    parentOrg: item.group.parentOrg?.name,
                  });
                  item.form.fromDateMenu = false;
                "
              >
                Save
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-menu>
      </v-col>
      <v-col cols="2">
        <v-menu
          v-model="item.form.toDateMenu"
          :close-on-content-click="false"
          v-model:return-value="item.form.toDate"
          transition="scale-transition"
          offset-y
          min-width="290px"
        >
          <template v-slot:activator="{ props }">
            <button
              :disabled="isLocked"
              v-bind="props"
              class="v-small-dialog__activator"
            >
              <span class="grey--text text--darken-2">
                {{ formatDate(item.end) }}
              </span>
              <v-icon size="small" end> mdi-lead-pencil </v-icon>
            </button>
          </template>
          <v-card min-width="180">
            <v-card-text>
              <date-input
                v-model="item.form.toDate"
                :min="item.start"
                label="Date to"
                nudge-top="20"
                nudge-right="10"
              />
            </v-card-text>
            <v-card-actions class="pt-0">
              <v-spacer></v-spacer>
              <v-btn text color="primary" @click="item.form.toDateMenu = false">
                Cancel
              </v-btn>
              <v-btn
                :disabled="!item.form.toDate"
                color="primary"
                text
                @click="
                  $emit('updateEnrollment', {
                    fromDate: item.start,
                    toDate: item.end,
                    newToDate: item.form.toDate,
                    group: item.group.name,
                    parentOrg: item.group.parentOrg?.name,
                  });
                  item.form.toDateMenu = false;
                "
              >
                Save
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-menu>
      </v-col>
      <v-col class="d-flex justify-end align-center pr-1">
        <v-tooltip
          location="bottom"
          transition="expand-y-transition"
          open-delay="200"
        >
          <template v-slot:activator="{ props }">
            <v-btn
              v-if="item.group.numchild > 0"
              v-bind="props"
              :disabled="isLocked"
              aria-label="Add to team"
              icon="mdi-plus"
              size="small"
              variant="text"
              @click="$emit('openTeamModal', item.group.name)"
            >
            </v-btn>
          </template>
          <span>Add to team</span>
        </v-tooltip>
        <v-tooltip
          location="bottom"
          transition="expand-y-transition"
          open-delay="200"
        >
          <template v-slot:activator="{ props }">
            <v-btn
              v-bind="props"
              aria-label="Remove affiliation"
              icon="mdi-delete"
              size="small"
              variant="text"
              :disabled="isLocked"
              @click="
                $emit('withdraw', {
                  name: item.group.name,
                  fromDate: item.start,
                  toDate: item.end,
                  parentOrg: item.group.parentOrg?.name,
                })
              "
            >
            </v-btn>
          </template>
          <span>Remove affiliation</span>
        </v-tooltip>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import DateInput from "./DateInput.vue";

export default {
  name: "EnrollmentList",
  components: { DateInput },
  props: {
    enrollments: {
      type: Array,
      required: true,
    },
    compact: {
      type: Boolean,
      required: false,
      default: false,
    },
    isLocked: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      items: {},
    };
  },
  methods: {
    formatDate(dateTime) {
      return dateTime.split("T")[0];
    },
    createForms(enrollments) {
      return enrollments.map((enrollment) => {
        const form = {
          fromDate: enrollment.start.split("T")[0],
          fromDateMenu: false,
          toDate: enrollment.end.split("T")[0],
          toDateMenu: false,
        };

        return Object.assign({}, enrollment, { form });
      });
    },
    withdrawAll() {
      this.enrollments.forEach((enrollment) => {
        this.$emit("withdraw", {
          name: enrollment.group.name,
          fromDate: enrollment.start,
          toDate: enrollment.end,
          parentOrg: enrollment.group.parentOrg
            ? enrollment.group.parentOrg.name
            : null,
        });
      });
    },
  },
  watch: {
    enrollments(value) {
      this.items = this.createForms(value);
    },
  },
  created() {
    this.items = this.createForms(this.enrollments);
  },
};
</script>

<style lang="scss" scoped>
@use "../styles/index.scss";
.indented {
  margin-left: 56px;
  margin-right: 12px;

  &:not(:last-child) {
    border-bottom: 1px solid #e5e5e5;
  }
}

li {
  list-style-type: none;
  padding: 8px;
  padding-left: 16px;
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
:deep(.v-small-dialog__activator) {
  display: inline-block;
}

.v-col {
  display: flex;
  align-items: center;
  padding-bottom: 4px;

  &-1 {
    max-width: 33px;
  }
}
</style>
