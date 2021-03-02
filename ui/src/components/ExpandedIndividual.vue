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
    <v-subheader class="d-flex justify-space-between">
      <span>Identities ({{ identitiesCount }})</span>
      <v-btn
        v-if="!compact"
        text
        small
        outlined
        :disabled="identitiesCount === 1 || isLocked"
        @click="splitAll"
      >
        <v-icon small left>mdi-call-split</v-icon>
        Split all
      </v-btn>
    </v-subheader>
    <v-simple-table v-if="compact" dense>
      <template v-slot:default>
        <thead v-if="identitiesCount > 0">
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">Email</th>
            <th class="text-left">Username</th>
            <th class="text-left">Source</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in flatIdentities" :key="item.uuid">
            <td>{{ item.name || "-" }}</td>
            <td>{{ item.email || "-" }}</td>
            <td>{{ item.username || "-" }}</td>
            <td>
              <v-tooltip
                bottom
                transition="expand-y-transition"
                open-delay="300"
              >
                <template v-slot:activator="{ on }">
                  <v-icon v-on="on" v-text="item.icon" small left />
                </template>
                <span>{{ item.source.toLowerCase() }}</span>
              </v-tooltip>
            </td>
          </tr>
        </tbody>
      </template>
    </v-simple-table>
    <v-list
      v-else
      v-for="(source, sourceIndex) in identities"
      :key="source.name"
      :class="{
        'row-border': sourceIndex !== identities.length - 1
      }"
      class="indented"
      dense
    >
      <v-list-item
        v-for="(identity, index) in sortSources(source.identities, 'source')"
        :class="{ draggable: identity.uuid !== uuid }"
        :key="identity.uuid"
        :draggable="identity.uuid !== uuid"
        @dragstart.native="startDrag(identity, $event)"
        @dragend.native="dragEnd($event)"
      >
        <v-list-item-icon v-if="index === 0">
          <v-tooltip bottom transition="expand-y-transition" open-delay="300">
            <template v-slot:activator="{ on }">
              <v-icon v-on="on">
                {{ source.icon }}
              </v-icon>
            </template>
            <span>
              {{ source.name }}
            </span>
          </v-tooltip>
        </v-list-item-icon>

        <v-list-item-action v-else></v-list-item-action>

        <v-list-item-content>
          <identity
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
            :source="identity.source || source.name"
          />
        </v-list-item-content>

        <v-tooltip bottom transition="expand-y-transition" open-delay="200">
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              :disabled="identity.uuid === uuid || isLocked"
              v-on="on"
              @click="$emit('unmerge', [identity.uuid, uuid])"
            >
              <v-icon>
                mdi-call-split
              </v-icon>
            </v-btn>
          </template>
          <span>Split identity</span>
        </v-tooltip>
        <v-tooltip bottom transition="expand-y-transition" open-delay="200">
          <template v-slot:activator="{ on }">
            <v-icon :disabled="identity.uuid === uuid" v-on="on">
              mdi-drag-vertical
            </v-icon>
          </template>
          <span>Move identity</span>
        </v-tooltip>
      </v-list-item>
    </v-list>

    <v-subheader class="d-flex justify-space-between">
      Organizations ({{ enrollments.length }})
      <v-btn
        v-if="!compact"
        text
        small
        outlined
        :disabled="enrollments.length < 1 || isLocked"
        @click="withdrawAll"
      >
        <v-icon small left>mdi-delete</v-icon>
        Remove all
      </v-btn>
    </v-subheader>
    <v-simple-table v-if="compact" dense>
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
            <td>{{ enrollment.organization.name }}</td>
            <td>{{ formatDate(enrollment.start) }}</td>
            <td>{{ formatDate(enrollment.end) }}</td>
          </tr>
        </tbody>
      </template>
    </v-simple-table>
    <v-list v-else class="indented" dense>
      <v-list-item
        v-for="(enrollment, index) in enrollments"
        :key="enrollment.organization.id"
        class="row-border"
      >
        <v-list-item-content>
          <v-row no-gutters class="flex align-center">
            <v-col>
              <span>{{ enrollment.organization.name }}</span>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span v-if="isLocked">
                {{ formatDate(enrollment.start) }}
              </span>
              <v-menu
                v-else
                v-model="enrollmentsForm[index].fromDateMenu"
                :close-on-content-click="false"
                :return-value.sync="enrollmentsForm[index].fromDate"
                transition="scale-transition"
                offset-y
                min-width="290px"
              >
                <template v-slot:activator="{ on, attrs }">
                  <button
                    v-on="on"
                    v-bind="attrs"
                    class="v-small-dialog__activator"
                  >
                    {{ formatDate(enrollment.start) }}
                    <v-icon small right>
                      mdi-lead-pencil
                    </v-icon>
                  </button>
                </template>
                <v-date-picker
                  v-model="enrollmentsForm[index].fromDate"
                  :max="enrollment.end"
                  color="primary"
                  no-title
                  scrollable
                >
                  <v-spacer></v-spacer>
                  <v-btn
                    text
                    color="primary"
                    @click="enrollmentsForm[index].fromDateMenu = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    text
                    color="primary"
                    @click="
                      $emit('updateEnrollment', {
                        fromDate: enrollment.start,
                        toDate: enrollment.end,
                        newFromDate: new Date(
                          enrollmentsForm[index].fromDate
                        ).toISOString(),
                        organization: enrollment.organization.name,
                        uuid: uuid
                      });
                      enrollmentsForm[index].fromDateMenu = false;
                    "
                  >
                    Save
                  </v-btn>
                </v-date-picker>
              </v-menu>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span v-if="isLocked">
                {{ formatDate(enrollment.end) }}
              </span>
              <v-menu
                v-else
                v-model="enrollmentsForm[index].toDateMenu"
                :close-on-content-click="false"
                :return-value.sync="enrollmentsForm[index].toate"
                transition="scale-transition"
                offset-y
                min-width="290px"
              >
                <template v-slot:activator="{ on, attrs }">
                  <button
                    v-on="on"
                    v-bind="attrs"
                    class="v-small-dialog__activator"
                  >
                    {{ formatDate(enrollment.end) }}
                    <v-icon small right>
                      mdi-lead-pencil
                    </v-icon>
                  </button>
                </template>
                <v-date-picker
                  v-model="enrollmentsForm[index].toDate"
                  :min="enrollment.start"
                  color="primary"
                  no-title
                  scrollable
                >
                  <v-spacer></v-spacer>
                  <v-btn
                    text
                    color="primary"
                    @click="enrollmentsForm[index].toDateMenu = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    text
                    color="primary"
                    @click="
                      $emit('updateEnrollment', {
                        fromDate: enrollment.start,
                        toDate: enrollment.end,
                        newToDate: new Date(
                          enrollmentsForm[index].toDate
                        ).toISOString(),
                        organization: enrollment.organization.name,
                        uuid: uuid
                      });
                      enrollmentsForm[index].toDateMenu = false;
                    "
                  >
                    Save
                  </v-btn>
                </v-date-picker>
              </v-menu>
            </v-col>
            <v-col class="text-end col-2">
              <v-tooltip
                bottom
                transition="expand-y-transition"
                open-delay="200"
              >
                <template v-slot:activator="{ on }">
                  <v-btn
                    icon
                    v-on="on"
                    :disabled="isLocked"
                    @click="
                      $emit('withdraw', {
                        name: enrollment.organization.name,
                        fromDate: enrollment.start,
                        toDate: enrollment.end
                      })
                    "
                  >
                    <v-icon>
                      mdi-delete
                    </v-icon>
                  </v-btn>
                </template>
                <span>Remove affiliation</span>
              </v-tooltip>
            </v-col>
          </v-row>
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <v-card class="dragged-identity" color="primary" dark>
      <v-card-subtitle> Moving 1 identity</v-card-subtitle>
    </v-card>
  </td>
</template>

<script>
import Identity from "./Identity.vue";

export default {
  name: "ExpandedIndividual",
  components: {
    Identity
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
    formatDate(dateTime) {
      return dateTime.split("T")[0];
    },
    sortSources(identities, property) {
      return identities.slice().sort((a, b) => {
        const sourceA = a[property].toLowerCase();
        const sourceB = b[property].toLowerCase();

        return sourceA.localeCompare(sourceB);
      });
    },
    startDrag(identity, event) {
      const dragImage = document.querySelector(".dragged-identity");
      event.dataTransfer.setDragImage(dragImage, 0, 0);
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("type", "move");
      event.dataTransfer.setData("uuid", identity.uuid);
      event.target.classList.add("dragging");
    },
    dragEnd(event) {
      event.target.classList.remove("dragging");
    },
    async getCountryList() {
      const response = await this.getCountries();
      if (response) {
        this.countries = response;
      }
    },
    splitAll() {
      const uuids = this.flatIdentities.map(identity => identity.uuid);
      this.$emit("unmerge", uuids);
    },
    withdrawAll() {
      this.enrollments.forEach(enrollment => {
        this.$emit("withdraw", {
          name: enrollment.organization.name,
          fromDate: enrollment.start,
          toDate: enrollment.end
        });
      });
    }
  },
  computed: {
    identitiesCount() {
      return this.identities.reduce((a, b) => a + b.identities.length, 0);
    },
    sources() {
      return this.identities.map(identity => identity.name);
    },
    flatIdentities() {
      return this.identities
        .map(source =>
          source.identities.map(identity =>
            Object.assign({ icon: source.icon }, identity)
          )
        )
        .flat();
    }
  },
  created() {
    this.enrollments.forEach(enrollment => {
      this.enrollmentsForm.push({
        fromDate: this.formatDate(enrollment.start),
        fromDateMenu: false,
        toDate: this.formatDate(enrollment.end),
        toDateMenu: false
      });
    });
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.indented {
  margin-left: 40px;
  background-color: transparent;
}

.draggable {
  cursor: pointer;

  &:hover {
    background: #eeeeee;
  }
}

.dragged-identity {
  max-width: 300px;
  position: absolute;
  top: -300px;
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
