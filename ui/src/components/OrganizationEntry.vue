<template>
  <tr>
    <td class="text--body-1">{{ name }}</td>
    <td class="text-right text--secondary">{{ enrollments }}</td>
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
    }
  }
};
</script>
