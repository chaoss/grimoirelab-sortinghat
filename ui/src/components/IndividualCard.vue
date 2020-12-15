<template>
  <v-card
    class="mx-auto"
    :class="{
      dropzone: isDragging,
      selected: isSelected,
      highlighted: isHighlighted
    }"
    raised
    v-on="$listeners"
    @drop.native.prevent.stop="onDrop($event)"
    @dragover.prevent.stop="isDragging = true"
    @dragenter.prevent.stop="isDragging = true"
    @dragleave="isDragging = false"
    @click="selectIndividual"
  >
    <v-list-item class="grow" three-line>
      <v-list-item-avatar color="grey lighten-2" size="30px">
        <span class="grey--text text--darken-3">{{ getNameInitials }}</span>
      </v-list-item-avatar>

      <v-list-item-content>
        <v-list-item-title class="font-weight-medium">
          {{ name || identities[0].identities[0].email }}
        </v-list-item-title>
        <v-list-item-subtitle v-if="enrollments && enrollments.length > 0">
          {{ enrollments[0].organization.name }}
        </v-list-item-subtitle>
        <v-list-item-subtitle>
          <v-icon
            v-for="source in sources"
            :key="source.name"
            v-text="selectSourceIcon(source)"
            small
            left
          />
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
import ExpandedIndividual from "./ExpandedIndividual";

export default {
  name: "individualcard",
  components: {
    ExpandedIndividual
  },
  props: {
    name: {
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
    }
  },
  data() {
    return {
      isDragging: false
    };
  },
  computed: {
    getNameInitials: function() {
      const name = this.name || this.identities[0].identities[0].email || "";
      const names = name.split(" ");
      let initials = names[0].substring(0, 1).toUpperCase();

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
    onDrop(event) {
      const type = event.dataTransfer.getData("type");
      if (type === "move") {
        this.moveIndividual(event);
      } else if (type === "enrollFromOrganization") {
        this.enrollIndividual(event);
      } else {
        this.mergeIndividuals(event);
      }
      this.isDragging = false;
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
      const uuids = droppedIndividuals.map(individual => individual.uuid);
      this.$emit("merge", [this.uuid, ...uuids]);
    },
    enrollIndividual(event) {
      const organization = event.dataTransfer.getData("organization");
      this.$emit("enroll", organization);
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
