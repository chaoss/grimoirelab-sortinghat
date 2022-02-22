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

    <enrollment-list
      :enrollments="enrollments"
      :compact="compact"
      :is-locked="isLocked"
      @openModal="$emit('openModal', { uuid, organization: $event })"
      @updateEnrollment="
        $emit('updateEnrollment', Object.assign($event, { uuid: uuid }))
      "
      @withdraw="$emit('withdraw', $event)"
    />

    <v-card class="dragged-identity" color="primary" dark>
      <v-card-subtitle> Moving 1 identity</v-card-subtitle>
    </v-card>
  </td>
</template>

<script>
import Identity from "./Identity.vue";
import EnrollmentList from "./EnrollmentList.vue";

export default {
  name: "ExpandedIndividual",
  components: {
    Identity,
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
