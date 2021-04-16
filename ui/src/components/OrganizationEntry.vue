<template>
  <tr
    :class="{ dropzone: dropZone }"
    @drop.stop="onDrop($event)"
    @dragover.prevent="isDropZone($event, true)"
    @dragenter.prevent="isDropZone($event, true)"
    @dragleave.prevent="isDropZone($event, false)"
  >
    <td class="font-weight-medium">{{ name }}</td>
    <td class="text-right text--secondary">
      <v-tooltip bottom transition="expand-y-transition" open-delay="200">
        <template v-slot:activator="{ on }">
          <v-btn
            depressed
            color="transparent"
            v-on="on"
            @click.stop="$emit('getEnrollments')"
          >
            {{ enrollments }}
            <v-icon small right>
              mdi-account-multiple
            </v-icon>
          </v-btn>
        </template>
        <span>Enrollments</span>
      </v-tooltip>
    </td>
    <td class="text-right">
      <v-btn icon @click.stop="$emit('edit')">
        <v-icon small>
          mdi-lead-pencil
        </v-icon>
      </v-btn>
      <v-btn icon @click.stop="$emit('delete')">
        <v-icon small>
          mdi-delete
        </v-icon>
      </v-btn>
      <v-btn icon @click.stop="$emit('expand')">
        <v-icon>
          {{ isExpanded ? "mdi-chevron-up" : "mdi-chevron-down" }}
        </v-icon>
      </v-btn>
    </td>
  </tr>
</template>

<script>
export default {
  name: "OrganizationEntry",
  props: {
    name: {
      type: String,
      required: true
    },
    enrollments: {
      type: Number,
      required: true
    },
    isExpanded: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      dropZone: false
    };
  },
  methods: {
    onDrop(event) {
      this.dropZone = false;
      const type = event.dataTransfer.getData("type");
      if (type === "enrollFromOrganization") {
        return;
      }
      const droppedIndividuals = JSON.parse(
        event.dataTransfer.getData("individuals")
      ).filter(individual => !individual.isLocked);
      if (droppedIndividuals.length > 0) {
        this.$emit("enroll", {
          uuids: droppedIndividuals.map(individual => individual.uuid),
          organization: this.name
        });
      }
    },
    isDropZone(event, isDragging) {
      const type = event.dataTransfer.getData("type");
      // Can't use 'getData' while dragging on Chrome
      const types = event.dataTransfer.types;

      // Prevents an organization from being drag&dropped into another one
      if (
        isDragging &&
        type !== "enrollFromOrganization" &&
        !types.includes("organization") &&
        !types.includes("lockactions")
      ) {
        this.dropZone = true;
      } else {
        this.dropZone = false;
      }
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
tr {
  cursor: pointer;
}
</style>
