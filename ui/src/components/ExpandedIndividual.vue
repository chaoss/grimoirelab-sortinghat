<template>
  <td :class="{ compact: compact }" colspan="4">
    <v-subheader v-if="!compact">Profile</v-subheader>
    <v-row v-if="!compact" class="ml-12">
      <p class="ml-2">
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
      </p>
      <p class="ml-6">
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
      </p>
    </v-row>
    <v-subheader>Identities ({{ identitiesCount }})</v-subheader>
    <v-list
      v-for="(source, sourceIndex) in sortSources(identities, 'name')"
      :key="source.name"
      class="indented"
    >
      <v-list-item
        v-for="(identity, index) in sortSources(source.identities, 'source')"
        :class="{ draggable: !compact && identity.uuid !== uuid }"
        :key="identity.uuid"
        :draggable="!compact && identity.uuid !== uuid"
        @dragstart.native="startDrag(identity, $event)"
        @dragend.native="dragEnd($event)"
      >
        <v-list-item-icon v-if="index === 0 && !compact">
          <v-icon>
            {{ selectSourceIcon(source.name) }}
          </v-icon>
        </v-list-item-icon>

        <v-list-item-action v-else-if="!compact"></v-list-item-action>

        <v-list-item-content>
          <identity
            :uuid="identity.uuid"
            :name="identity.name"
            :email="identity.email"
            :username="identity.username"
            :source="identity.source || source.name"
          />
        </v-list-item-content>

        <div v-if="!compact">
          <v-tooltip bottom transition="expand-y-transition" open-delay="200">
            <template v-slot:activator="{ on }">
              <v-btn
                icon
                :disabled="identity.uuid === uuid"
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
        </div>
      </v-list-item>
      <v-divider
        inset
        v-if="sourceIndex !== identities.length - 1 && !compact"
      ></v-divider>
    </v-list>

    <v-divider v-if="!compact" inset class="divider"></v-divider>

    <v-list>
      <v-subheader>Organizations ({{ enrollments.length }})</v-subheader>

      <v-list-item
        v-for="(enrollment, index) in enrollments"
        :key="enrollment.organization.id"
      >
        <v-list-item-content>
          <v-row no-gutters>
            <v-col class="ma-2 text-center">
              <span>{{ enrollment.organization.name }}</span>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span v-if="isLocked || compact">
                {{ formatDate(enrollment.start) }}
              </span>
              <v-edit-dialog
                v-else
                @close="
                  $emit('updateEnrollment', {
                    fromDate: enrollment.start,
                    toDate: enrollment.end,
                    newFromDate: new Date(
                      enrollmentsForm[index].fromDate
                    ).toISOString(),
                    organization: enrollment.organization.name,
                    uuid: uuid
                  })
                "
              >
                {{ formatDate(enrollment.start) }}
                <v-icon small right>
                  mdi-lead-pencil
                </v-icon>
                <template v-slot:input>
                  <v-menu
                    v-model="enrollmentsForm[index].fromDateMenu"
                    :close-on-content-click="false"
                    transition="scale-transition"
                    offset-y
                    min-width="290px"
                  >
                    <template v-slot:activator="{ on }">
                      <v-text-field
                        v-model="enrollmentsForm[index].fromDate"
                        readonly
                        v-on="on"
                      ></v-text-field>
                    </template>
                    <v-date-picker
                      v-model="enrollmentsForm[index].fromDate"
                      @input="enrollmentsForm[index].fromDateMenu = false"
                      no-title
                      scrollable
                    >
                    </v-date-picker>
                  </v-menu>
                </template>
              </v-edit-dialog>
            </v-col>
            <v-col class="col-3 ma-2 text-center">
              <span v-if="isLocked || compact">
                {{ formatDate(enrollment.end) }}
              </span>
              <v-edit-dialog
                v-else
                @close="
                  $emit('updateEnrollment', {
                    fromDate: enrollment.start,
                    toDate: enrollment.end,
                    newToDate: new Date(
                      enrollmentsForm[index].toDate
                    ).toISOString(),
                    organization: enrollment.organization.name,
                    uuid: uuid
                  })
                "
              >
                {{ formatDate(enrollment.end) }}
                <v-icon small right>
                  mdi-lead-pencil
                </v-icon>
                <template v-slot:input>
                  <v-menu
                    v-model="enrollmentsForm[index].toDateMenu"
                    :close-on-content-click="false"
                    transition="scale-transition"
                    offset-y
                    min-width="290px"
                  >
                    <template v-slot:activator="{ on }">
                      <v-text-field
                        v-model="enrollmentsForm[index].toDate"
                        readonly
                        v-on="on"
                      ></v-text-field>
                    </template>
                    <v-date-picker
                      v-model="enrollmentsForm[index].toDate"
                      @input="enrollmentsForm[index].toDateMenu = false"
                      no-title
                      scrollable
                    >
                    </v-date-picker>
                  </v-menu>
                </template>
              </v-edit-dialog>
            </v-col>
          </v-row>
        </v-list-item-content>
      </v-list-item>
    </v-list>

    <v-card class="dragged-item" color="primary" dark>
      <v-card-title> Moving 1</v-card-title>
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
    selectSourceIcon(source) {
      var datasource = source.toLowerCase();

      if (datasource === "github") {
        return "mdi-github";
      } else if (datasource === "git") {
        return "mdi-git";
      } else if (datasource === "gitlab") {
        return "mdi-gitlab";
      } else if (datasource === "others") {
        return "mdi-account-multiple";
      }
    },
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
      const dragImage = document.querySelector(".dragged-item");
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
    }
  },
  computed: {
    identitiesCount() {
      return this.identities.reduce((a, b) => a + b.identities.length, 0);
    },
    sources() {
      return this.identities.map(identity => identity.name);
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
td {
  padding-left: 75px;
  border-bottom: thin solid rgba(0, 0, 0, 0.12);
}

.indented {
  margin: 0 40px;
}

.v-application--is-ltr .v-divider--inset:not(.v-divider--vertical).divider {
  width: calc(100% - 30px);
  max-width: calc(100% - 30px);
  margin-left: 30px;
}

.draggable {
  cursor: pointer;

  &:hover {
    background: #eeeeee;
  }
}

.dragged-item {
  max-width: 300px;
  position: absolute;
  top: -300px;
}

.compact {
  padding-left: 0;
  border-bottom: 0;
  background-color: #ffffff;
  font-size: 0.9rem;
  line-height: 1rem;
  padding: 0;

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
