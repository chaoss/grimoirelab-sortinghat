<template>
  <div class="d-flex flex-column justify-center align-center pa-4 h-100">
    <v-progress-circular :size="size" color="primary" indeterminate />
    <p v-if="label" class="subtitle-1 text-medium-emphasis mt-4">{{ label }}</p>
  </div>
</template>
<script>
export default {
  name: "LoadingSpinner",
  props: {
    label: {
      type: String,
      required: false,
      default: null,
    },
    size: {
      type: [String, Number],
      required: false,
      default: 48,
    },
  },
};
</script>
