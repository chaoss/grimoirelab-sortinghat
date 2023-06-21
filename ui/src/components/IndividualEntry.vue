<template>
  <tr
    :aria-selected="isSelected"
    :class="{
      expanded: isExpanded,
      selected: isSelected,
      dropzone: isDropZone,
      highlighted: isHighlighted,
    }"
    @click.prevent="selectEntry"
    @dblclick="onDoubleClick"
    @drop.stop="onDrop($event)"
    @dragover.prevent="handleDrag($event, true)"
    @dragenter.prevent="handleDrag($event, true)"
    @dragleave.prevent="handleDrag($event, false)"
    @mouseenter="$emit('highlight')"
    @mouseleave="$emit('stopHighlight')"
  >
    <td width="25%">
      <v-list-item>
        <avatar :name="name" :email="email" class="mt-3 mb-3" />

        <v-list-item-content>
          <v-list-item-title class="font-weight-medium">
            <router-link
              :to="{ name: 'Individual', params: { mk: uuid } }"
              target="_blank"
            >
              <span @click.stop>{{ name || "no name" }}</span>
            </router-link>

            <v-tooltip bottom transition="expand-y-transition" open-delay="200">
              <template v-slot:activator="{ on }">
                <v-icon
                  v-show="!isLocked"
                  v-on="on"
                  class="aligned"
                  :class="{ 'icon--hidden': !isBot }"
                  small
                  right
                  @click.stop="$emit('edit', { isBot: !isBot })"
                >
                  mdi-robot
                </v-icon>
                <v-icon
                  v-show="isLocked && isBot"
                  v-on="on"
                  class="aligned"
                  small
                  right
                >
                  mdi-robot
                </v-icon>
              </template>
              <span>Bot</span>
            </v-tooltip>

            <v-tooltip bottom transition="expand-y-transition" open-delay="200">
              <template v-slot:activator="{ on }">
                <v-hover v-slot="{ hover }">
                  <v-icon
                    v-on="on"
                    class="aligned"
                    :class="{ 'icon--hidden': !isLocked }"
                    small
                    right
                    @click.stop="$emit('lock', !isLocked)"
                  >
                    {{ hover && isLocked ? "mdi-lock-open" : "mdi-lock" }}
                  </v-icon>
                </v-hover>
              </template>
              <span>{{ isLocked ? "Unlock profile" : "Lock profile" }}</span>
            </v-tooltip>
          </v-list-item-title>
          <v-list-item-subtitle v-if="organization">
            {{ organization }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </td>

    <td class="text-center">
      <span>{{ email }}</span>
    </td>

    <td class="text-right">
      <v-tooltip
        v-for="(source, index) in sources"
        :key="index"
        bottom
        transition="expand-y-transition"
        open-delay="300"
      >
        <template v-slot:activator="{ on }">
          <v-chip v-on="on" class="ml-1" outlined>
            <v-icon v-text="source.icon" left />
            {{ source.count }}
          </v-chip>
        </template>
        <span>{{ source.name }}</span>
      </v-tooltip>
    </td>

    <td v-if="isExpandable" width="140">
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
          <v-list-item :href="`individual/${uuid}`" target="_blank">
            <v-list-item-title> View full profile </v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('select', $event)">
            <v-list-item-title>
              {{ isSelected ? "Deselect individual" : "Select individual" }}
            </v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('saveIndividuals')">
            <v-list-item-title>Save in workspace</v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('openMatchesModal', $event)">
            <v-list-item-title> Recommend matches </v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('delete', $event)" :disabled="isLocked">
            <v-list-item-title>Delete individual</v-list-item-title>
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
import Avatar from "./Avatar.vue";
export default {
  name: "IndividualEntry",
  components: {
    Avatar,
  },
  props: {
    name: {
      type: String,
      required: false,
    },
    organization: {
      type: String,
      required: false,
    },
    email: {
      type: String,
      required: false,
    },
    sources: {
      type: Array,
      required: false,
    },
    uuid: {
      type: String,
      required: true,
    },
    isExpanded: {
      type: Boolean,
      required: true,
    },
    isLocked: {
      type: Boolean,
      required: true,
    },
    isBot: {
      type: Boolean,
      required: true,
    },
    isSelected: {
      type: Boolean,
      required: false,
      default: false,
    },
    isHighlighted: {
      type: Boolean,
      required: false,
      default: false,
    },
    isExpandable: {
      type: Boolean,
      required: false,
    },
  },
  data() {
    return {
      isDragging: false,
      form: {
        name: this.name,
        email: this.email,
      },
      timeout: null,
    };
  },
  computed: {
    isDropZone: function () {
      return this.isDragging && !this.isLocked;
    },
  },
  methods: {
    selectEntry() {
      const delay = 350;
      if (!this.timeout) {
        this.timeout = window.setTimeout(() => {
          this.timeout = null;
          this.$emit("select");
        }, delay);
      }
    },
    onDoubleClick() {
      window.clearTimeout(this.timeout);
      this.timeout = null;
    },
    onDrop(event) {
      this.isDragging = false;
      if (this.isLocked) {
        return;
      }
      const type = event.dataTransfer.getData("type");
      if (type === "move") {
        this.moveIndividual(event);
      } else if (event.dataTransfer.getData("group")) {
        this.enrollIndividual(event);
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
        droppedIndividuals
          .filter((individual) => !individual.isLocked)
          .map((individual) => individual.uuid)
      );
    },
    moveIndividual(event) {
      const uuid = event.dataTransfer.getData("uuid");
      this.$emit("move", { fromUuid: uuid, toUuid: this.uuid });
    },
    enrollIndividual(event) {
      const group = event.dataTransfer.getData("group");
      const parentOrg = event.dataTransfer.getData("parentorg");
      this.$emit("enroll", { group, parentOrg });
    },
    handleDrag(event, isDragging) {
      const types = event.dataTransfer.types;

      if (isDragging && !types.includes("lockactions")) {
        this.isDragging = true;
      } else {
        this.isDragging = false;
      }
    },
  },
  watch: {
    name(value) {
      this.form.name = value;
    },
    email(value) {
      this.form.email = value;
    },
  },
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
  ::v-deep .icon--hidden {
    opacity: 0;
    padding-bottom: 2px;
  }
  &:hover {
    ::v-deep .icon--hidden {
      opacity: 1;
    }
  }
}

.v-list-item__title {
  a {
    color: rgba(0, 0, 0, 0.87);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
