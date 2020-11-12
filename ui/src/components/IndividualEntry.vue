<template>
  <tr
    :class="{
      expanded: isExpanded,
      selected: isSelected,
      dropzone: isDropZone,
      highlighted: isHighlighted
    }"
    @click="selectEntry"
    @drop.stop="onDrop($event)"
    @dragover.prevent="isDragging = true"
    @dragenter.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @mouseenter="$emit('highlight')"
    @mouseleave="$emit('stopHighlight')"
  >
    <td width="25%">
      <v-list-item>
        <v-list-item-avatar color="grey lighten-2">
          <span class="grey--text text--darken-3">{{ getNameInitials }}</span>
        </v-list-item-avatar>

        <v-list-item-content>
          <v-list-item-title>
            {{ name }}
            <v-tooltip
              v-if="isBot"
              bottom
              transition="expand-y-transition"
              open-delay="200"
            >
              <template v-slot:activator="{ on }">
                <v-icon v-on="on" class="aligned" small right>
                  mdi-robot
                </v-icon>
              </template>
              <span>Bot</span>
            </v-tooltip>
            <v-tooltip
              v-if="isLocked"
              bottom
              transition="expand-y-transition"
              open-delay="200"
            >
              <template v-slot:activator="{ on }">
                <v-icon v-on="on" class="aligned" small right>
                  mdi-lock
                </v-icon>
              </template>
              <span>Locked profile</span>
            </v-tooltip>
          </v-list-item-title>
          <v-list-item-subtitle>{{ organization }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </td>
    <td class="text-center">
      {{ email }}
    </td>
    <td class="text-right">
      <v-icon
        v-for="source in sortedSources"
        :key="source.name"
        v-text="selectSourceIcon(source)"
        left
        right
      />
    </td>
    <td width="140">
      <v-btn icon @click.stop="$emit('expand')">
        <v-icon>
          {{ isExpanded ? "mdi-chevron-up" : "mdi-chevron-down" }}
        </v-icon>
      </v-btn>
      <v-menu right nudge-right="35">
        <template v-slot:activator="{ on, attrs }">
          <v-btn icon v-bind="attrs" v-on="on">
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <v-list>
          <v-list-item @click="$emit('saveIndividual', $event)">
            <v-list-item-title>Save in workspace</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('delete', $event)" :disabled="isLocked">
            <v-list-item-title>Delete profile</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      <v-tooltip bottom transition="expand-y-transition" open-delay="200">
        <template v-slot:activator="{ on }">
          <v-icon :disabled="isLocked" v-on="on">mdi-drag-vertical</v-icon>
        </template>
        <span>Drag individual</span>
      </v-tooltip>
    </td>
  </tr>
</template>
<script>
export default {
  name: "IndividualEntry",
  props: {
    name: {
      type: String,
      required: false
    },
    organization: {
      type: String,
      required: false
    },
    email: {
      type: String,
      required: false
    },
    sources: {
      type: Array,
      required: false
    },
    uuid: {
      type: String,
      required: true
    },
    isExpanded: {
      type: Boolean,
      required: true
    },
    isLocked: {
      type: Boolean,
      required: true
    },
    isBot: {
      type: Boolean,
      required: true
    },
    isSelected: {
      type: Boolean,
      required: false,
      default: false
    },
    isHighlighted: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data: () => ({
    isDragging: false
  }),
  computed: {
    getNameInitials: function() {
      const name = this.name || this.email || "";
      const names = name.split(" ");
      let initials = names[0].substring(0, 1).toUpperCase();

      if (names.length > 1) {
        initials += names[names.length - 1].substring(0, 1).toUpperCase();
      }

      return initials;
    },
    isDropZone: function() {
      return this.isDragging && !this.isLocked;
    },
    sortedSources: function() {
      return this.sources.slice().sort();
    }
  },
  methods: {
    selectSourceIcon(source) {
      const datasource = source.toLowerCase();

      if (datasource === "others") {
        return "mdi-account-multiple";
      } else {
        return `mdi-${datasource}`;
      }
    },
    selectEntry() {
      if (this.isLocked) {
        return;
      }
      this.$emit("select");
    },
    onDrop(event) {
      this.isDragging = false;
      if (this.isLocked) {
        return;
      }
      const type = event.dataTransfer.getData("type");
      if (type === "move") {
        this.moveIndividual(event);
      } else {
        this.mergeIndividuals(event);
      }
    },
    mergeIndividuals(event) {
      const droppedIndividuals = JSON.parse(
        event.dataTransfer.getData("individuals")
      );
      this.$emit(
        "merge",
        droppedIndividuals.map(individual => individual.uuid)
      );
    },
    moveIndividual(event) {
      const uuid = event.dataTransfer.getData("uuid");
      this.$emit("move", { fromUuid: uuid, toUuid: this.uuid });
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";

.theme--light.v-data-table tbody .expanded td:not(.v-data-table__mobile-row) {
  border: 0;
}
.v-list-item__title {
  text-overflow: inherit;
}
.aligned {
  margin-bottom: 4px;
}
.theme--light.v-data-table tbody tr:not(:last-child).selected td {
  border-bottom: 0;
}
tr {
  cursor: pointer;
}
</style>
