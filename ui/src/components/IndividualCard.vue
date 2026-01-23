<template>
  <v-card
    class="mx-auto"
    :class="{
      locked: isLocked,
      dropzone: isDragging,
      selected: isSelected && !recommendation,
      highlighted: isHighlighted,
      disabled: !selectable,
      'selected--merge': state.merge,
      'selected--dismiss': state.dismiss,
    }"
    :ripple="selectable"
    v-bind="$attrs"
    @drop.prevent.stop="onDrop($event)"
    @dragover.prevent.stop="isDropZone($event, true)"
    @dragenter.prevent.stop="isDropZone($event, true)"
    @dragleave="isDropZone($event, false)"
    @click="selectIndividual"
  >
    <template v-slot:prepend>
      <avatar :name="name" :email="email" :size="30" />
    </template>

    <template v-slot:item>
      <v-list-item class="grow pa-2" lines="three">
        <v-list-item-title class="font-weight-medium">
          <router-link
            :to="{ name: 'Individual', params: { mk: uuid } }"
            target="_blank"
            class="link--underline"
          >
            <span @click.stop>{{ name || email }}</span>
          </router-link>
        </v-list-item-title>
        <v-list-item-subtitle v-if="organization">
          {{ organization }}
        </v-list-item-subtitle>
        <v-list-item-subtitle v-if="!detailed">
          <v-tooltip
            v-for="source in sources"
            :key="source.name"
            location="bottom"
            transition="expand-y-transition"
            open-delay="300"
          >
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" size="small" start>
                {{ source.icon }}
              </v-icon>
            </template>
            <span>{{ source.name }}</span>
          </v-tooltip>
        </v-list-item-subtitle>
        <div v-if="detailed">
          <v-list-item-subtitle v-for="(email, i) in emails" :key="i">
            <v-icon size="x-small" class="mr-1">mdi-email-outline</v-icon>
            {{ email }}
          </v-list-item-subtitle>
          <template v-for="username in usernames">
            <v-list-item-subtitle
              v-for="(name, icon) in JSON.parse(username)"
              :key="icon"
            >
              <v-icon size="x-small" class="mr-1">{{ icon }}</v-icon>
              {{ name }}
            </v-list-item-subtitle>
          </template>
        </div>
      </v-list-item>
    </template>

    <template v-slot:append>
      <v-icon v-if="isLocked" size="x-small" class="mr-2">mdi-lock</v-icon>
      <v-menu offset="4" location="right" :close-on-content-click="false">
        <template v-slot:activator="{ props }">
          <v-btn
            variant="text"
            class="mr-1"
            density="compact"
            icon="mdi-magnify-plus-outline"
            v-bind="props"
            data-cy="expand-button"
            aria-label="Expand information"
            @mousedown.stop
            @keyup.stop
          />
        </template>
        <v-card class="pa-1">
          <expanded-individual
            compact
            :enrollments="enrollments"
            :identities="identities"
            :uuid="uuid"
          />
        </v-card>
      </v-menu>
      <v-btn
        v-if="closable"
        icon="mdi-close"
        density="compact"
        variant="text"
        aria-label="Remove"
        @click.stop="$emit('remove')"
        @mousedown.stop
      />
    </template>
    <template v-if="recommendation" v-slot:actions>
      <v-spacer />
      <v-btn
        :color="state.dismiss ? 'red-darken-2' : 'default'"
        class="v-chip v-chip--label text-caption"
        variant="tonal"
        size="small"
        @click="handleDismiss"
      >
        <v-icon start>mdi-close</v-icon>
        Keep separate
      </v-btn>
      <v-btn
        :color="state.merge ? 'light-green-darken-2' : 'default'"
        class="v-chip v-chip--label text-caption"
        variant="tonal"
        size="small"
        @click="handleMerge"
      >
        <v-icon start>mdi-call-merge</v-icon>
        Merge
      </v-btn>
    </template>
    <slot />
  </v-card>
</template>

<script>
import Avatar from "./Avatar.vue";
import ExpandedIndividual from "./ExpandedIndividual.vue";

export default {
  name: "individualcard",
  components: {
    Avatar,
    ExpandedIndividual,
  },
  props: {
    name: {
      type: String,
      required: false,
      default: null,
    },
    email: {
      type: String,
      required: false,
      default: null,
    },
    sources: {
      type: Array,
      required: false,
      default: () => [],
    },
    isSelected: {
      type: Boolean,
      required: false,
      default: false,
    },
    uuid: {
      type: String,
      required: true,
    },
    identities: {
      type: Array,
      required: false,
    },
    enrollments: {
      type: Array,
      required: false,
    },
    isHighlighted: {
      type: Boolean,
      required: false,
      default: false,
    },
    isLocked: {
      type: Boolean,
      required: false,
      default: false,
    },
    closable: {
      type: Boolean,
      required: false,
    },
    selectable: {
      type: Boolean,
      required: false,
    },
    emails: {
      type: [Set, Array],
      required: false,
    },
    usernames: {
      type: [Set, Array],
      required: false,
    },
    detailed: {
      type: Boolean,
      required: false,
      default: false,
    },
    recommendation: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      isDragging: false,
      state: {
        merge: false,
        dismiss: false,
      },
    };
  },
  computed: {
    organization() {
      if (this.enrollments && this.enrollments.length > 0) {
        return this.enrollments.findLast(
          (enrollment) => !enrollment.group.parentOrg
        ).group.name;
      }
      return null;
    },
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
    selectIndividual() {
      this.$emit("select");
    },
    moveIndividual(event) {
      const uuid = event.dataTransfer.getData("uuid");
      this.$emit("move", { fromUuid: uuid, toUuid: this.uuid });
    },
    mergeIndividuals(event) {
      const droppedIndividuals = JSON.parse(
        event.dataTransfer.getData("individuals")
      );
      const uuids = droppedIndividuals
        .filter((individual) => !individual.isLocked)
        .map((individual) => individual.uuid);
      if (uuids.length > 0) {
        this.$emit("merge", [this.uuid, ...uuids]);
      }
    },
    enrollIndividual(event) {
      const group = event.dataTransfer.getData("group");
      const parentOrg = event.dataTransfer.getData("parentorg");
      this.$emit("enroll", { group, parentOrg });
    },
    isDropZone(event, isDragging) {
      const types = event.dataTransfer.types;

      if (isDragging && !types.includes("lockactions")) {
        this.isDragging = true;
      } else {
        this.isDragging = false;
      }
    },
    handleMerge() {
      if (this.state.merge) {
        this.state.merge = false;
        this.$emit("apply", null);
      } else {
        this.state.merge = true;
        this.$emit("apply", true);
        if (this.state.dismiss) {
          this.state.dismiss = false;
        }
      }
    },
    handleDismiss() {
      if (this.state.dismiss) {
        this.state.dismiss = false;
        this.$emit("apply", null);
      } else {
        this.state.dismiss = true;
        this.$emit("apply", false);
        if (this.state.merge) {
          this.state.merge = false;
        }
      }
    },
  },
};
</script>
<style lang="scss" scoped>
@use "../styles/index.scss";

:deep(.v-card-item) {
  align-items: baseline;

  .v-card-item__content {
    align-self: unset;

    .v-list-item__content {
      align-self: start;
    }

    .v-list-item-subtitle {
      line-height: 1.2rem;
    }
  }
}

.v-card-item__append {
  .v-btn--icon {
    margin-top: 1px;
  }
}

.v-avatar.v-avatar--density-default {
  font-size: 0.8rem;
}

.disabled {
  cursor: default;
}

.v-list-item--density-default.v-list-item--three-line {
  min-height: 78px;
}

.v-card--variant-outlined {
  border-color: rgba(0, 0, 0, 0.08);

  .v-card-item .v-card-item__content .v-list-item-subtitle {
    line-height: 1.3rem;
    opacity: 0.7;
  }
}

.v-card.selected--merge {
  background-color: #f1f8e9;
}

.v-card.selected--dismiss {
  background-color: #ffebee;
}

.v-card-actions {
  padding-top: 0;
}
</style>
