<template>
  <div>
    <v-list-subheader>
      <span class="text-subtitle-2">
        Organizations ({{ Object.keys(items).length }})
      </span>
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
    <div v-else v-for="(item, name) in items" :key="name" class="ma-4">
      <div
        v-for="(enrollment, index) in item.enrollments"
        :key="index"
        class="mb-2 d-flex justify-space-between align-center"
      >
        <div>
          <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" class="mr-3"> mdi-sitemap </v-icon>
            </template>
            <span>Organization</span>
          </v-tooltip>
          {{ name }}

          <v-menu
            v-model="enrollment.form.fromDateMenu"
            :close-on-content-click="false"
            v-model:return-value="enrollment.form.fromDate"
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
                <span class="grey--text text--darken-2 ml-6">
                  {{ formatDate(enrollment.start) }}
                </span>
                <v-icon size="small" end> mdi-lead-pencil </v-icon>
              </button>
            </template>
            <v-card min-width="180">
              <v-card-text>
                <date-input
                  v-model="enrollment.form.fromDate"
                  label="Date from"
                  nudge-top="20"
                  nudge-right="10"
                  :max="enrollment.end"
                />
              </v-card-text>
              <v-card-actions class="pt-0">
                <v-spacer></v-spacer>
                <v-btn
                  text
                  color="primary"
                  @click="enrollment.form.fromDateMenu = false"
                >
                  Cancel
                </v-btn>
                <v-btn
                  :disabled="!enrollment.form.fromDate"
                  color="primary"
                  text
                  @click="
                    $emit('updateEnrollment', {
                      fromDate: enrollment.start,
                      toDate: enrollment.end,
                      newFromDate: enrollment.form.fromDate,
                      group: enrollment.group.name,
                    });
                    enrollment.form.fromDateMenu = false;
                  "
                >
                  Save
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-menu>
          <v-menu
            v-model="enrollment.form.toDateMenu"
            :close-on-content-click="false"
            v-model:return-value="enrollment.form.toDate"
            transition="scale-transition"
            offset-y
            min-width="290px"
          >
            <template v-slot:activator="{ props }">
              <button
                :disabled="isLocked"
                v-bind="props"
                class="v-small-dialog__activator ml-5"
              >
                <span class="grey--text text--darken-2 ml-2">
                  {{ formatDate(enrollment.end) }}
                </span>
                <v-icon size="small" end> mdi-lead-pencil </v-icon>
              </button>
            </template>
            <v-card min-width="180">
              <v-card-text>
                <date-input
                  v-model="enrollment.form.toDate"
                  :min="enrollment.start"
                  label="Date to"
                  nudge-top="20"
                  nudge-right="10"
                />
              </v-card-text>
              <v-card-actions class="pt-0">
                <v-spacer></v-spacer>
                <v-btn
                  text
                  color="primary"
                  @click="enrollment.form.toDateMenu = false"
                >
                  Cancel
                </v-btn>
                <v-btn
                  :disabled="!enrollment.form.toDate"
                  color="primary"
                  text
                  @click="
                    $emit('updateEnrollment', {
                      fromDate: enrollment.start,
                      toDate: enrollment.end,
                      newToDate: enrollment.form.toDate,
                      group: enrollment.group.name,
                    });
                    enrollment.form.toDateMenu = false;
                  "
                >
                  Save
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-menu>
        </div>
        <div>
          <v-tooltip
            location="bottom"
            transition="expand-y-transition"
            open-delay="200"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                :disabled="isLocked"
                icon="mdi-account-multiple-plus"
                variant="text"
                v-bind="props"
                @click="$emit('openTeamModal', enrollment.group.name)"
              />
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
                icon="mdi-delete"
                v-bind="props"
                variant="text"
                :disabled="isLocked"
                @click="
                  $emit('withdraw', {
                    name: enrollment.group.name,
                    fromDate: enrollment.start,
                    toDate: enrollment.end,
                  })
                "
              />
            </template>
            <span>Remove affiliation</span>
          </v-tooltip>
        </div>
      </div>

      <ul class="ma-2 mr-0">
        <li
          v-for="team in item.teams"
          :key="team.group.name"
          class="d-flex justify-space-between pr-0"
        >
          <div class="d-flex align-center">
            <span class="ml-3 mr-4">{{ team.group.name }}</span>

            <v-menu
              v-model="team.form.fromDateMenu"
              :close-on-content-click="false"
              v-model:return-value="team.form.fromDate"
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
                  <span class="grey--text text--darken-2 ml-6">
                    {{ formatDate(team.start) }}
                  </span>
                  <v-icon size="small" end> mdi-lead-pencil </v-icon>
                </button>
              </template>
              <v-card min-width="180">
                <v-card-text>
                  <date-input
                    v-model="team.form.fromDate"
                    :max="team.end"
                    label="Date to"
                    nudge-top="20"
                    nudge-right="10"
                  />
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    text
                    color="primary"
                    @click="team.form.fromDateMenu = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    text
                    color="primary"
                    @click="
                      $emit('updateEnrollment', {
                        fromDate: team.start,
                        toDate: team.end,
                        newFromDate: new Date(team.form.fromDate).toISOString(),
                        group: team.group.name,
                        parentOrg: team.group.parentOrg.name,
                      });
                      team.form.fromDateMenu = false;
                    "
                  >
                    Save
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-menu>
            -
            <v-menu
              v-model="team.form.toDateMenu"
              :close-on-content-click="false"
              v-model:return-value="team.form.toDate"
              transition="scale-transition"
              offset-y
              min-width="290px"
            >
              <template v-slot:activator="{ props }">
                <button
                  :disabled="isLocked"
                  v-bind="props"
                  class="v-small-dialog__activator ml-5"
                >
                  <span class="grey--text text--darken-2 ml-2">
                    {{ formatDate(team.end) }}
                  </span>
                  <v-icon size="small" end> mdi-lead-pencil </v-icon>
                </button>
              </template>
              <v-card min-width="180">
                <v-card-text>
                  <date-input
                    v-model="team.form.toDate"
                    :min="team.start"
                    label="Date to"
                    nudge-top="20"
                    nudge-right="10"
                  />
                </v-card-text>
                <v-card-actions class="pt-0">
                  <v-spacer></v-spacer>
                  <v-btn
                    text
                    color="primary"
                    @click="team.form.toDateMenu = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    :disabled="!team.form.toDate"
                    color="primary"
                    text
                    @click="
                      $emit('updateEnrollment', {
                        fromDate: team.start,
                        toDate: team.end,
                        newToDate: new Date(team.form.toDate).toISOString(),
                        group: team.group.name,
                        parentOrg: team.group.parentOrg.name,
                      });
                      team.form.toDateMenu = false;
                    "
                  >
                    Save
                  </v-btn>
                </v-card-actions>
              </v-card>
            </v-menu>
          </div>

          <v-tooltip
            location="bottom"
            transition="expand-y-transition"
            open-delay="200"
          >
            <template v-slot:activator="{ props }">
              <v-btn
                :disabled="isLocked"
                icon="mdi-delete"
                variant="text"
                v-bind="props"
                @click="
                  $emit('withdraw', {
                    name: team.group.name,
                    fromDate: team.start,
                    toDate: team.end,
                    parentOrg: team.group.parentOrg.name,
                  })
                "
              />
            </template>
            <span>Remove affiliation</span>
          </v-tooltip>
        </li>
      </ul>
    </div>
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
    groupEnrollments(enrollments) {
      return enrollments.reduce(function (acc, obj) {
        const form = {
          fromDate: obj.start.split("T")[0],
          fromDateMenu: false,
          toDate: obj.end.split("T")[0],
          toDateMenu: false,
        };

        if (obj.group.parentOrg) {
          const parent = obj.group.parentOrg.name;
          if (!acc[parent]) {
            acc[parent] = {
              enrollments: [],
              teams: [],
            };
          }
          obj = Object.assign({}, obj, { form: form });
          acc[parent].teams.push(obj);
        } else {
          const key = obj.group.name;
          if (!acc[key]) {
            acc[key] = {
              enrollments: [],
              teams: [],
            };
          }
          obj = Object.assign({}, obj, { form: form });
          acc[key].enrollments.push(obj);
        }
        return acc;
      }, {});
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
      this.items = this.groupEnrollments(value);
    },
  },
  created() {
    this.items = this.groupEnrollments(this.enrollments);
  },
};
</script>

<style lang="scss" scoped>
@import "../styles/index.scss";
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
</style>
