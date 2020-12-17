<template>
  <tr
    :class="{ dropzone: dropZone }"
    @drop.stop="onDrop($event)"
    @dragover.prevent="isDropZone($event, true)"
    @dragenter.prevent="isDropZone($event, true)"
    @dragleave.prevent="isDropZone($event, false)"
  >
    <td class="text--body-1">{{ name }}</td>
    <td class="text-right text--secondary">
      {{ enrollments }}
      <v-tooltip bottom transition="expand-y-transition" open-delay="200">
        <template v-slot:activator="{ on }">
          <v-icon v-on="on" small right>
            mdi-account-multiple
          </v-icon>
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
      );
      this.$emit("enroll", {
        uuids: droppedIndividuals.map(individual => individual.uuid),
        organization: this.name
      });
    },
    isDropZone(event, isDragging) {
      const type = event.dataTransfer.getData("type");
      // Can't use 'getData' while dragging on Chrome
      const types = event.dataTransfer.types;

      // Prevents an organization from being drag&dropped into another one
      if (
        isDragging &&
        type !== "enrollFromOrganization" &&
        !types.includes("organization")
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
