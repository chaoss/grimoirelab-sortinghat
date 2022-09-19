<template>
  <div>
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
        :class="{ draggable: draggable && identity.uuid !== uuid }"
        :key="identity.uuid"
        :draggable="draggable && !isLocked && identity.uuid !== uuid"
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
            :is-main="identity.uuid === uuid"
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
            <v-icon
              v-if="draggable"
              :disabled="identity.uuid === uuid || isLocked"
              v-on="on"
            >
              mdi-drag-vertical
            </v-icon>
          </template>
          <span>Move identity</span>
        </v-tooltip>
      </v-list-item>
    </v-list>
    <v-card class="dragged-identity" color="primary" dark>
      <v-card-subtitle> Moving 1 identity</v-card-subtitle>
    </v-card>
  </div>
</template>

<script>
import Identity from "./Identity.vue";

export default {
  name: "IdentitiesList",
  components: {
    Identity
  },
  props: {
    identities: {
      type: Array,
      required: true
    },
    isLocked: {
      type: Boolean,
      required: false,
      default: false
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
    draggable: {
      type: Boolean,
      required: false,
      default: false
    }
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
</style>
