<template>
  <v-sheet
    class="section"
    data-cy="workspace"
    :class="{ 'is-dragging': isDragging }"
    @drop="onDrop($event)"
    @dragover.prevent="onDrag($event)"
    @dragenter.prevent="onDrag($event)"
    @dragleave.prevent="isDragging = false"
  >
    <v-row class="header">
      <h3 class="title">
        <v-icon color="black" size="small" start> mdi-pin </v-icon>
        Workspace
      </h3>
      <div>
        <v-btn
          variant="outlined"
          size="small"
          class="mr-2"
          :disabled="isDisabled"
          @click="mergeSelected(selectedIndividuals)"
        >
          <v-icon size="small" start>mdi-call-merge</v-icon>
          Merge
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          :disabled="savedIndividuals.length === 0"
          @click="clearSpace"
        >
          <v-icon size="small" start>mdi-cancel</v-icon>
          Clear
        </v-btn>
      </div>
    </v-row>
    <ul class="grid drag-zone" v-if="savedIndividuals.length >= 1">
      <li v-for="individual in savedIndividuals" :key="individual.id">
        <individual-card
          tabindex="0"
          :name="individual.name"
          :email="individual.email"
          :sources="individual.sources"
          :is-selected="isSelected(individual)"
          :uuid="individual.uuid"
          :identities="individual.identities"
          :enrollments="individual.enrollments"
          :is-highlighted="individual.uuid === highlightIndividual"
          :is-locked="individual.isLocked"
          :aria-pressed="isSelected(individual)"
          @enroll="confirmEnroll(individual, $event)"
          @keyup.enter="selectIndividual(individual)"
          @merge="mergeSelected($event)"
          @mouseenter="$emit('highlight', individual)"
          @mouseleave="$emit('stopHighlight', individual)"
          @move="move($event)"
          @remove="removeIndividual(individual)"
          @select="selectIndividual(individual)"
          closable
          selectable
        />
      </li>
    </ul>
    <v-row
      v-else
      dense
      class="align-center justify-center drag-zone"
    >
      <v-icon color="rgba(0,0,0,0.38)" left> mdi-lightbulb-on-outline </v-icon>
      <p class="mb-0 ml-2 text-medium-emphasis">
        <span>
          You can add individuals to your work space to perform actions on them
          later.
        </span>
        <span>
          For example, to merge individuals from different searches.
        </span>
      </p>
    </v-row>

    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p v-if="dialog.text" class="pt-2 pb-2 text-body-2">
            {{ dialog.text }}
          </p>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog"> Cancel </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog"> OK </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <enroll-modal
      v-model:is-open="enrollmentModal.open"
      :title="enrollmentModal.title"
      :text="enrollmentModal.text"
      :organization="enrollmentModal.organization"
      :uuid="enrollmentModal.uuid"
      :enroll="enrollIndividual"
    />

    <team-enroll-modal
      v-if="teamModal.isOpen"
      v-model:is-open="teamModal.isOpen"
      :organization="teamModal.organization"
      :team="teamModal.team"
      :uuid="teamModal.uuid"
      :enrollments="teamModal.enrollments"
      :enroll="enrollIndividual"
    />
  </v-sheet>
</template>

<script>
import {
  mergeIndividuals,
  moveIdentity,
  formatIndividuals,
} from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import IndividualCard from "./IndividualCard.vue";
import EnrollModal from "./EnrollModal.vue";
import TeamEnrollModal from "./TeamEnrollModal.vue";

export default {
  name: "WorkSpace",
  components: {
    IndividualCard,
    EnrollModal,
    TeamEnrollModal,
  },
  mixins: [enrollMixin],
  props: {
    highlightIndividual: {
      type: String,
      required: false,
    },
    individuals: {
      type: Array,
      required: true,
    },
    mergeItems: {
      type: Function,
      required: true,
    },
    moveItem: {
      type: Function,
      required: true,
    },
    enroll: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      savedIndividuals: this.individuals,
      selectedIndividuals: [],
      isDragging: false,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: "",
      },
    };
  },
  computed: {
    isDisabled() {
      return (
        this.selectedIndividuals.filter((individual) => !individual.isLocked)
          .length < 2
      );
    },
  },
  methods: {
    clearSpace() {
      this.savedIndividuals = [];
      this.$emit("clearSpace");
    },
    onDrop(evt) {
      const type = evt.dataTransfer.getData("type");
      const types = evt.dataTransfer.types;
      if (type === "move" || types.includes("group")) {
        return;
      }
      const droppedIndividuals = JSON.parse(
        evt.dataTransfer.getData("individuals")
      );
      const newIndividuals = droppedIndividuals
        .filter(
          (dropped) =>
            !this.savedIndividuals.some(
              (individual) => individual.id === dropped.id
            )
        )
        .map((individual) => Object.assign(individual, { isSelected: false }));
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
        this.$emit("updateWorkspace", {
          update: this.savedIndividuals,
          remove: fromUuids,
        });
        this.$logger.debug("Merged individuals", { fromUuids, toUuid });
        this.selectedIndividuals = [];
      }
      this.dialog.open = false;
    },
    mergeSelected(individuals) {
      individuals = individuals.filter((individual) => !individual.isLocked);
      mergeIndividuals(individuals, this.merge, this.dialog);
    },
    updateMergedIndividuals(updated, mergedIndividuals) {
      const updatedIndividual = formatIndividuals([updated.individual])[0];
      const updatedIndex = this.savedIndividuals.findIndex(
        (individual) => individual.id === updatedIndividual.id
      );
      Object.assign(this.savedIndividuals[updatedIndex], updatedIndividual);
      const individuals = this.savedIndividuals.filter(
        (individual) => !mergedIndividuals.includes(individual.uuid)
      );
      return individuals;
    },
    selectIndividual(individual) {
      const index = this.selectedIndividuals.findIndex(
        (saved) => individual.uuid === saved.uuid
      );

      if (index === -1) {
        this.selectedIndividuals.push(individual);
      } else {
        this.selectedIndividuals.splice(index, 1);
      }
    },
    isSelected(individual) {
      return this.selectedIndividuals.some(
        (saved) => saved.uuid === individual.uuid
      );
    },
    removeIndividual(individual) {
      this.savedIndividuals = this.savedIndividuals.filter(
        (savedIndividual) => savedIndividual.uuid !== individual.uuid
      );
      if (this.isSelected(individual)) {
        this.selectIndividual(individual);
      }
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
          this.$logger.debug("Moved identity", { fromUuid, toUuid });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error("Error moving identity: ${error}", {
          fromUuid,
          toUuid,
        });
      }
    },
    onDrag(event) {
      const type = event.dataTransfer.getData("type");
      const types = event.dataTransfer.types;
      if (type === "move" || types.includes("group")) {
        return;
      }
      this.isDragging = true;
    },
    closeDialog() {
      Object.assign(this.dialog, {
        open: false,
        title: "",
        text: "",
        action: "",
      });
    },
  },
  watch: {
    individuals: {
      handler(value) {
        this.savedIndividuals = value;
      },
      deep: true,
    },
    savedIndividuals: {
      handler(value) {
        if (value) {
          this.$emit("updateStore", value);
        }
      },
      deep: true,
    },
  },
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
.drag-zone {
  min-height: 146px;
  transition: background-color 0.1s;
}
.is-dragging .drag-zone {
  outline: 1px dashed #003756;
  background-color: #f9edc7;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr));
  grid-column-gap: 1rem;
  grid-row-gap: 1rem;
  padding: 1.5rem;

  li {
    list-style: none;
  }
}
</style>
