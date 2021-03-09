<template>
  <tr
    :aria-selected="isSelected"
    :class="{
      expanded: isExpanded,
      selected: isSelected,
      dropzone: isDropZone,
      highlighted: isHighlighted
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
        <avatar :name="name" :email="email" />

        <v-list-item-content>
          <v-list-item-title class="font-weight-medium">
            <span v-if="isLocked">{{ name }}</span>
            <v-edit-dialog v-else @save="$emit('edit', { name: form.name })">
              {{ name }}
              <v-icon class="icon--hidden" small>
                mdi-lead-pencil
              </v-icon>
              <template v-slot:input>
                <v-text-field
                  v-model="form.name"
                  label="Edit name"
                  maxlength="30"
                  single-line
                ></v-text-field>
              </template>
            </v-edit-dialog>

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
                <v-icon
                  v-on="on"
                  class="aligned"
                  :class="{ 'icon--hidden': !isLocked }"
                  small
                  right
                  @click.stop="$emit('lock', !isLocked)"
                >
                  mdi-lock
                </v-icon>
              </template>
              <span>{{ isLocked ? "Unlock profile" : "Lock profile" }}</span>
            </v-tooltip>
          </v-list-item-title>
          <v-list-item-subtitle>{{ organization }}</v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </td>

    <td class="text-center">
      <span v-if="isLocked" class="mr-7">{{ email }}</span>
      <v-edit-dialog v-else @save="$emit('edit', { email: form.email })">
        {{ email }}
        <v-icon small right>
          mdi-lead-pencil
        </v-icon>
        <template v-slot:input>
          <v-text-field
            v-model="form.email"
            label="Edit email"
            maxlength="30"
            single-line
          ></v-text-field>
        </template>
      </v-edit-dialog>
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
          <v-icon v-on="on" v-text="source.icon" left right />
        </template>
        <span>{{ source.name }}</span>
      </v-tooltip>
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
          <v-list-item @click="$emit('select', $event)">
            <v-list-item-title>
              {{ isSelected ? "Deselect individual" : "Select individual" }}
            </v-list-item-title>
          </v-list-item>
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
import Avatar from "./Avatar.vue";
export default {
  name: "IndividualEntry",
  components: {
    Avatar
  },
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
  data() {
    return {
      isDragging: false,
      form: {
        name: this.name,
        email: this.email
      },
      timeout: null
    };
  },
  computed: {
    isDropZone: function() {
      return this.isDragging && !this.isLocked;
    }
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
      } else if (type === "enrollFromOrganization") {
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
          .filter(individual => !individual.isLocked)
          .map(individual => individual.uuid)
      );
    },
    moveIndividual(event) {
      const uuid = event.dataTransfer.getData("uuid");
      this.$emit("move", { fromUuid: uuid, toUuid: this.uuid });
    },
    enrollIndividual(event) {
      const organization = event.dataTransfer.getData("organization");
      this.$emit("enroll", organization);
    },
    handleDrag(event, isDragging) {
      const types = event.dataTransfer.types;

      if (isDragging && !types.includes("lockactions")) {
        this.isDragging = true;
      } else {
        this.isDragging = false;
      }
    }
  },
  watch: {
    name(value) {
      this.form.name = value;
    },
    email(value) {
      this.form.email = value;
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
::v-deep .v-small-dialog__activator,
.v-small-dialog {
  display: inline-block;
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
.v-list-item__title {
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
</style>
