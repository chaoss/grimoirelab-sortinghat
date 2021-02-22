<template>
  <v-sheet
    color="#F5F5F6"
    class="pa-md-4"
    :class="{ 'is-dragging': isDragging }"
    @drop.native="onDrop($event)"
    @dragover.prevent="onDrag($event)"
    @dragenter.prevent="onDrag($event)"
    @dragleave.prevent="isDragging = false"
  >
    <v-row class="ma-md-0 pt-md-4 pl-md-4 pr-md-4 justify-space-between">
      <h3 class="title">
        <v-icon color="black" left>
          mdi-pin
        </v-icon>
        Workspace
      </h3>
      <div>
        <v-tooltip bottom transition="expand-y-transition" open-delay="200">
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              v-on="on"
              :disabled="selectedIndividuals.length < 2"
              @click="mergeSelected(selectedIndividuals)"
            >
              <v-icon>mdi-call-merge</v-icon>
            </v-btn>
          </template>
          <span>Merge selected</span>
        </v-tooltip>
        <v-tooltip left transition="expand-y-transition" open-delay="200">
          <template v-slot:activator="{ on }">
            <v-btn
              :disabled="savedIndividuals.length === 0"
              v-on="on"
              icon
              @click="clearSpace"
            >
              <v-icon>mdi-delete-sweep</v-icon>
            </v-btn>
          </template>
          <span>Clear space</span>
        </v-tooltip>
      </div>
    </v-row>
    <v-row
      v-if="savedIndividuals.length >= 1"
      dense
      class="pa-md-4 ma-md-0 drag-zone"
    >
      <v-col
        v-for="individual in savedIndividuals"
        :key="individual.id"
        cols="2"
      >
        <individual-card
          :name="individual.name"
          :email="individual.email"
          :sources="individual.sources"
          :is-selected="individual.isSelected"
          :uuid="individual.uuid"
          :identities="individual.identities"
          :enrollments="individual.enrollments"
          :is-highlighted="individual.uuid === highlightIndividual"
          @enroll="confirmEnroll(individual.uuid, $event)"
          @merge="mergeSelected($event)"
          @mouseenter="$emit('highlight', individual)"
          @mouseleave="$emit('stopHighlight', individual)"
          @move="move($event)"
          @remove="removeIndividual(individual)"
          @select="selectIndividual(individual)"
        />
      </v-col>
    </v-row>
    <v-row v-else dense class="pa-md-5 ma-md-0 d-flex align-center drag-zone">
      <p class="text--disabled">
        Save individuals in your work space to perform actions on them.
      </p>
    </v-row>

    <v-snackbar v-model="snackbar.open">
      {{ snackbar.text }}
    </v-snackbar>

    <v-dialog v-model="dialog.open" max-width="400">
      <v-card>
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>{{ dialog.text }}</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialog.open = false">
            Cancel
          </v-btn>
          <v-btn color="blue darken-4" text @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-sheet>
</template>

<script>
import {
  mergeIndividuals,
  moveIdentity,
  formatIndividuals
} from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import IndividualCard from "./IndividualCard.vue";
export default {
  name: "WorkSpace",
  components: {
    IndividualCard
  },
  mixins: [enrollMixin],
  props: {
    highlightIndividual: {
      type: String,
      required: false
    },
    individuals: {
      type: Array,
      required: true
    },
    mergeItems: {
      type: Function,
      required: true
    },
    moveItem: {
      type: Function,
      required: true
    },
    enroll: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      savedIndividuals: this.individuals,
      isDragging: false,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: ""
      },
      snackbar: {
        open: false,
        text: ""
      }
    };
  },
  computed: {
    selectedIndividuals() {
      return this.savedIndividuals.filter(individual => individual.isSelected);
    }
  },
  methods: {
    clearSpace() {
      this.savedIndividuals = [];
      this.$emit("clearSpace");
    },
    onDrop(evt) {
      const type = evt.dataTransfer.getData("type");
      if (type === "move" || type === "enrollFromOrganization") {
        return;
      }
      const droppedIndividuals = JSON.parse(
        evt.dataTransfer.getData("individuals")
      );
      const newIndividuals = droppedIndividuals
        .filter(
          dropped =>
            !this.savedIndividuals.some(
              individual => individual.id === dropped.id
            )
        )
        .map(individual => Object.assign(individual, { isSelected: false }));
      this.savedIndividuals.push(...newIndividuals);
      this.isDragging = false;
      this.$emit("deselect");
    },
    async merge(fromUuids, toUuid) {
      const response = await this.mergeItems(fromUuids, toUuid);
      if (response) {
        this.savedIndividuals = this.updateMergedIndividuals(
          response.data.merge,
          fromUuids
        );
        this.$emit("updateIndividuals");
      }
      this.dialog.open = false;
    },
    mergeSelected(individuals) {
      mergeIndividuals(individuals, this.merge, this.dialog);
    },
    updateMergedIndividuals(updated, mergedIndividuals) {
      const updatedIndividual = formatIndividuals([updated.individual])[0];
      const updatedIndex = this.savedIndividuals.findIndex(
        individual => individual.id === updatedIndividual.id
      );
      Object.assign(this.savedIndividuals[updatedIndex], updatedIndividual);
      const individuals = this.savedIndividuals.filter(
        individual => !mergedIndividuals.includes(individual.uuid)
      );
      return individuals;
    },
    selectIndividual(individual) {
      individual.isSelected = !individual.isSelected;
    },
    removeIndividual(individual) {
      this.savedIndividuals = this.savedIndividuals.filter(
        savedIndividual => savedIndividual.uuid !== individual.uuid
      );
      this.$emit("updateWorkspace", { remove: [individual.uuid] });
      this.$emit("stopHighlight", individual);
    },
    move(event) {
      moveIdentity(event.fromUuid, event.toUuid, this.moveAction, this.dialog);
    },
    async moveAction(fromUuid, toUuid) {
      this.dialog.open = false;
      try {
        const response = await this.moveItem(fromUuid, toUuid);
        if (response) {
          this.savedIndividuals = this.updateMergedIndividuals(
            response.data.moveIdentity,
            [fromUuid]
          );
          this.$emit("updateIndividuals");
        }
      } catch (error) {
        Object.assign(this.snackbar, {
          open: true,
          text: error
        });
      }
    },
    onDrag(event) {
      const type = event.dataTransfer.getData("type");
      const types = event.dataTransfer.types;
      if (
        type === "move" ||
        type === "enrollFromOrganization" ||
        types.includes("organization")
      ) {
        return;
      }
      this.isDragging = true;
    }
  },
  watch: {
    individuals(value) {
      this.savedIndividuals = value;
    },
    savedIndividuals(value) {
      if (value) {
        this.$emit("updateStore", value);
      }
    }
  }
};
</script>
<style scoped>
.drag-zone {
  min-height: 128px;
}
.is-dragging .drag-zone {
  outline: 2px dashed #003756;
}
.col-2 {
  min-width: 300px;
}
</style>
