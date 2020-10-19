<template>
  <v-card
    class="mx-auto"
    :class="{ dropzone: isDragging }"
    raised
    v-on="$listeners"
    @drop.native.prevent.stop="onDrop($event)"
    @dragover.prevent.stop="isDragging = true"
    @dragenter.prevent.stop="isDragging = true"
    @dragleave="isDragging = false"
  >
    <v-list-item class="grow">
      <v-list-item-avatar color="grey">
        {{ getNameInitials }}
      </v-list-item-avatar>

      <v-list-item-content>
        <v-list-item-title>{{ name }}</v-list-item-title>
        <v-list-item-subtitle>
          <v-icon
            v-for="source in sources"
            :key="source.name"
            v-text="selectSourceIcon(source)"
            small
          />
        </v-list-item-subtitle>
      </v-list-item-content>

      <v-list-item-icon>
        <v-btn text icon @click.stop="toggleLockedStatus" @mousedown.stop>
          <v-icon small>
            {{ locked ? "mdi-lock" : "mdi-lock-open-outline" }}
          </v-icon>
        </v-btn>
      </v-list-item-icon>
    </v-list-item>
    <slot />
    <v-snackbar v-model="snackbar.value" color="error">
      {{ snackbar.text || "Error" }}
    </v-snackbar>
  </v-card>
</template>

<script>
import { lockIndividual, unlockIndividual } from "../apollo/mutations";

export default {
  name: "individualcard",
  props: {
    name: {
      type: String,
      required: true
    },
    sources: {
      type: Array,
      required: false,
      default: () => []
    },
    isLocked: {
      type: Boolean,
      required: false,
      default: false
    },
    uuid: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      locked: this.isLocked,
      snackbar: {
        value: false,
        text: ""
      },
      isDragging: false
    };
  },
  computed: {
    getNameInitials: function() {
      var names = this.name.split(" ");
      var initials = names[0].substring(0, 1).toUpperCase();

      if (names.length > 1) {
        initials += names[names.length - 1].substring(0, 1).toUpperCase();
      }

      return initials;
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
    async toggleLockedStatus() {
      if (this.$apollo) {
        try {
          const mutation = this.locked
            ? unlockIndividual(this.$apollo, this.uuid)
            : lockIndividual(this.$apollo, this.uuid);
          const response = await mutation;

          if (response && !response.errors) {
            this.locked = !this.locked;
          } else {
            this.snackbar = {
              value: true,
              text: response.errors[0].message
            };
          }
        } catch (error) {
          this.snackbar = {
            value: true,
            text: error.toString()
          };
        }
      } else if (this.$root.STORYBOOK_COMPONENT) {
        this.locked = !this.locked;
      }
    },
    onDrop(event) {
      const droppedIndividual = JSON.parse(
        event.dataTransfer.getData("individual")
      );
      if (this.uuid === droppedIndividual.uuid) {
        return;
      }
      this.$emit("merge", [this.uuid, droppedIndividual.uuid]);
      this.isDragging = false;
    }
  },
  watch: {
    isLocked(value) {
      this.locked = value;
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.selected {
  outline: rgba(25, 118, 210, 0.42) solid 2px;
  box-shadow: 0px 5px 5px -3px rgba(25, 118, 210, 0.2),
    0px 8px 10px 1px rgba(25, 118, 210, 0.14),
    0px 3px 14px 2px rgba(25, 118, 210, 0.12);
}
</style>
