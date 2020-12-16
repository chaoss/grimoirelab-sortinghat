<template>
  <v-sheet
    color="grey lighten-5"
    class="pa-md-4"
    :class="{ dragging: isDragging }"
    @drop.native="onDrop($event)"
    @dragover.prevent="onDrag($event)"
    @dragenter.prevent="onDrag($event)"
    @dragleave.prevent="isDragging = false"
  >
    <v-row class="ma-md-0 pt-md-4 pl-md-4 pr-md-4 justify-space-between">
      <h3 class="text-h6">
        <v-icon color="primary" left>
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
    <p v-else class="text--disabled pa-md-4 drag-zone">
      Save individuals in your work space to perform actions on them.
    </p>

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
  groupIdentities
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
      const updatedIndividual = {
        name: updated.individual.profile.name,
        isLocked: updated.individual.isLocked,
        uuid: updated.uuid,
        id: updated.individual.profile.id,
        sources: this.getSourceIcons(updated.individual.identities),
        isSelected: false,
        identities: groupIdentities(updated.individual.identities)
      };
      const updatedIndex = this.savedIndividuals.findIndex(
        individual => individual.id === updatedIndividual.id
      );
      Object.assign(this.savedIndividuals[updatedIndex], updatedIndividual);
      const individuals = this.savedIndividuals.filter(
        individual => !mergedIndividuals.includes(individual.uuid)
      );
      return individuals;
    },
    getSourceIcons(identities) {
      const icons = ["git", "github", "gitlab"];
      return [
        ...new Set(
          identities.map(item => {
            return icons.find(icon => icon === item.source.toLowerCase())
              ? item.source.toLowerCase()
              : "others";
          })
        )
      ];
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
    }
  }
};
</script>
<style scoped>
.text-h3 {
  font-size: 1.25rem;
  line-height: 2rem;
  font-weight: 500;
}
.dragging .drag-zone {
  outline: 2px dashed #bdbdbd;
}
.col-2 {
  min-width: 300px;
}
</style>
