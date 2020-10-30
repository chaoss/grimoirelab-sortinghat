<template>
  <tr
    :class="{ dropzone: isDragging }"
    @drop.stop="onDrop($event)"
    @dragover.prevent="isDragging = true"
    @dragenter.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
  >
    <td class="text--body-1">{{ name }}</td>
    <td class="text-right text--secondary">{{ enrollments }}</td>
    <td class="text-right" width="40">
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
      isDragging: false
    };
  },
  methods: {
    onDrop(event) {
      this.isDragging = false;
      const droppedIndividuals = JSON.parse(
        event.dataTransfer.getData("individuals")
      );
      this.$emit("enroll", {
        uuids: droppedIndividuals.map(individual => individual.uuid),
        organization: this.name
      });
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
</style>
