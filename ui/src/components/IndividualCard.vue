<template>
  <v-card class="mx-auto" raised>
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
        <v-btn text icon>
          <v-icon small @click="toggleLockedStatus">
            {{ locked ? "mdi-lock" : "mdi-lock-open-outline" }}
          </v-icon>
        </v-btn>
      </v-list-item-icon>
    </v-list-item>
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
      }
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

          if (response) {
            this.locked = !this.locked;
          }
        } catch (error) {
          this.snackbar = {
            value: true,
            text: error.toString()
          };
        }
      }
    }
  }
};
</script>
