<template>
  <v-sheet
    color="grey lighten-5"
    class="pa-md-4"
    :class="{ dragging: isDragging }"
    @drop.native="onDrop($event)"
    @dragover.prevent="isDragging = true"
    @dragenter.prevent="isDragging = true"
  >
    <v-row class="ma-md-0 pt-md-4 pl-md-4 pr-md-4 justify-space-between">
      <h3 class="text-h3">Work Space</h3>
      <div>
        <v-tooltip bottom transition="expand-y-transition" open-delay="200">
          <template v-slot:activator="{ on }">
            <v-btn
              icon
              v-on="on"
              :disabled="savedIndividuals.length < 2"
              @click="mergeSelected"
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
          :is-locked="individual.isLocked"
          :uuid="individual.uuid"
        />
      </v-col>
    </v-row>
    <p v-else class="text--disabled pa-md-4 drag-zone">
      Save individuals in your work space to perform actions on them.
    </p>

    <v-snackbar v-model="showSnackbar">
      Individual already in work space
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
import { mergeIndividuals } from "../utils/actions";
import IndividualCard from "./IndividualCard.vue";
export default {
  name: "WorkSpace",
  components: {
    IndividualCard
  },
  props: {
    individuals: {
      type: Array,
      required: true
    },
    mergeItems: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      savedIndividuals: this.individuals,
      isDragging: false,
      showSnackbar: false,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: ""
      }
    };
  },
  methods: {
    clearSpace() {
      this.savedIndividuals = [];
      this.$emit("clearSpace");
    },
    onDrop(evt) {
      const droppedIndividual = JSON.parse(
        evt.dataTransfer.getData("individual")
      );
      const isSaved = this.savedIndividuals.find(individual => {
        return individual.uuid === droppedIndividual.uuid;
      });
      if (isSaved) {
        this.showSnackbar = true;
        return;
      }
      this.savedIndividuals.push(droppedIndividual);
      this.isDragging = false;
    },
    async merge(fromUuids, toUuid) {
      const response = await this.mergeItems(fromUuids, toUuid);
      if (response) {
        this.savedIndividuals = [
          this.updateMergedIndividual(response.data.merge)
        ];
        this.$emit("updateIndividuals");
      }
      this.dialog.open = false;
    },
    mergeSelected() {
      mergeIndividuals(this.savedIndividuals, this.merge, this.dialog);
    },
    updateMergedIndividual(individual) {
      return {
        name: individual.individual.profile.name,
        isLocked: individual.individual.isLocked,
        uuid: individual.uuid,
        sources: this.getSourceIcons(individual.individual.identities)
      };
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
</style>
