<template>
  <v-list-item-avatar :color="getAvatarColor">
    <span class="white--text">{{ getNameInitials }}</span>
  </v-list-item-avatar>
</template>

<script>
const colors = [
  "#f41900",
  "#E35017",
  "#F58E0C",
  "#f4bc00",
  "#3fa500",
  "#436436",
  "#00a156",
  "#003756",
  "#0090E3",
  "#0B22E3",
  "#7218F5",
  "#6b00f4",
  "#3c0056",
  "#bc00f4",
  "#a5003f",
  "#F52537"
];
export default {
  props: {
    name: {
      type: String,
      required: false
    },
    email: {
      type: String,
      required: false
    }
  },
  computed: {
    getAvatarColor: function() {
      const charCodes = this.getNameInitials
        .split("")
        .map(char => char.charCodeAt(0))
        .join("");
      const index = charCodes % colors.length;

      return colors[index];
    },
    getNameInitials: function() {
      const name = this.name || this.email || "";
      const names = name.split(" ");
      let initials = names[0].substring(0, 1).toUpperCase();

      if (names.length > 1) {
        initials += names[names.length - 1].substring(0, 1).toUpperCase();
      }

      return initials;
    }
  }
}
</script>

<style scoped>
.v-avatar img {
  position: absolute;
}
</style>
