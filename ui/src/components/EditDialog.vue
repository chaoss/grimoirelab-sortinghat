<template>
  <v-menu v-model="menu" :close-on-content-click="false">
    <template v-slot:activator="{ props }">
      <button v-if="activator === 'text'" class="hide-icon" v-bind="props">
        <span v-if="modelValue">
          <slot name="value" v-bind="props">{{ modelValue }}</slot>
        </span>
        <span class="font-italic" v-else>
          {{ emptyValue }}
        </span>
        <v-icon class="icon--hidden ml-2" :aria-label="label" size="x-small">
          mdi-lead-pencil
        </v-icon>
      </button>
      <v-btn v-else v-bind="props" size="small" variant="outlined">
        <v-icon start>mdi-plus</v-icon>
        Add
      </v-btn>
    </template>
    <v-card min-width="250">
      <v-confirm-edit
        v-slot="{ model, actions }"
        :model-value="modelValue"
        ok-text="Save"
        @cancel="menu = false"
        @save="save($event)"
      >
        <v-card-text>
          <slot name="input" :model="model">
            <v-text-field
              v-model="model.value"
              :label="label"
              color="primary"
              density="compact"
              hide-details
              single-line
            />
          </slot>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <component color="primary" :is="actions" />
        </v-card-actions>
      </v-confirm-edit>
    </v-card>
  </v-menu>
</template>
<script>
export default {
  name: "EditDialog",
  props: {
    modelValue: {
      type: [String, Object],
      required: false,
    },
    label: {
      type: String,
      required: true,
    },
    activator: {
      type: String,
      required: false,
      default: "text",
    },
    emptyValue: {
      type: String,
      required: false,
    },
  },
  data: () => ({
    menu: false,
  }),
  methods: {
    save(event) {
      this.$emit("save", event);
      this.menu = false;
    },
  },
};
</script>
<style lang="scss" scoped>
.hide-icon {
  .icon--hidden {
    opacity: 0;
    transition: opacity 200ms;
    margin-bottom: 4px;
  }

  &:hover,
  &:focus {
    .icon--hidden {
      opacity: 1;
    }
  }
}
.v-btn--variant-outlined {
  border: thin solid rgba(0, 0, 0, 0.12);
}
</style>
