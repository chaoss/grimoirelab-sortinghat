<template>
  <v-card
    class="mx-auto"
    :class="{
      locked: isLocked,
      dropzone: isDragging,
      selected: isSelected,
      highlighted: isHighlighted
    }"
    raised
    v-on="$listeners"
    @drop.native.prevent.stop="onDrop($event)"
    @dragover.prevent.stop="isDropZone($event, true)"
    @dragenter.prevent.stop="isDropZone($event, true)"
    @dragleave="isDropZone($event, false)"
    @click="selectIndividual"
  >
    <v-list-item class="grow" three-line>
      <avatar :name="name" :email="email" :size="30" />

      <v-list-item-content>
        <v-list-item-title class="font-weight-medium">
          {{ name || email }}
          <v-icon v-if="isLocked" small right class="mb-1">mdi-lock</v-icon>
        </v-list-item-title>
        <v-list-item-subtitle v-if="enrollments && enrollments.length > 0">
          {{ enrollments[0].organization.name }}
        </v-list-item-subtitle>
        <v-list-item-subtitle>
          <v-tooltip
            v-for="source in sources"
            :key="source.name"
            bottom
            transition="expand-y-transition"
            open-delay="300"
          >
            <template v-slot:activator="{ on }">
              <v-icon v-on="on" v-text="source.icon" small left />
            </template>
            <span>{{ source.name }}</span>
          </v-tooltip>
        </v-list-item-subtitle>
      </v-list-item-content>

      <v-list-item-icon>
        <v-menu offset-y offset-x :close-on-content-click="false">
          <template v-slot:activator="{ on }">
            <v-btn icon v-on="on" @mousedown.stop>
              <v-icon small>
                mdi-magnify-plus-outline
              </v-icon>
            </v-btn>
          </template>
          <expanded-individual
            compact
            :enrollments="enrollments"
            :identities="identities"
            :uuid="uuid"
          />
        </v-menu>
        <v-btn text icon @click.stop="$emit('remove')" @mousedown.stop>
          <v-icon small>
            mdi-close
          </v-icon>
        </v-btn>
      </v-list-item-icon>
    </v-list-item>
    <slot />
  </v-card>
</template>

<script>
import Avatar from "./Avatar";
import ExpandedIndividual from "./ExpandedIndividual";

export default {
  name: "individualcard",
  components: {
    Avatar,
    ExpandedIndividual
  },
  props: {
    name: {
      type: String,
      required: false,
      default: null
    },
    email: {
      type: String,
      required: false,
      default: null
    },
    sources: {
      type: Array,
      required: false,
      default: () => []
    },
    isSelected: {
      type: Boolean,
      required: false,
      default: false
    },
    uuid: {
      type: String,
      required: true
    },
    identities: {
      type: Array,
      required: false
    },
    enrollments: {
      type: Array,
      required: false
    },
    isHighlighted: {
      type: Boolean,
      required: false,
      default: false
    },
    isLocked: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      isDragging: false
    };
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
      } else if (type === "enrollFromOrganization") {
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
        .filter(individual => !individual.isLocked)
        .map(individual => individual.uuid);
      if (uuids.length > 0) {
        this.$emit("merge", [this.uuid, ...uuids]);
      }
    },
    enrollIndividual(event) {
      const organization = event.dataTransfer.getData("organization");
      this.$emit("enroll", organization);
    },
    isDropZone(event, isDragging) {
      const types = event.dataTransfer.types;

      if (isDragging && !types.includes("lockactions")) {
        this.isDragging = true;
      } else {
        this.isDragging = false;
      }
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";

.v-list-item--three-line .v-list-item__avatar {
  font-size: 0.8rem;
}
</style>
