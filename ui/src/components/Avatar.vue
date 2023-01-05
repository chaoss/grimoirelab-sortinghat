<template>
  <v-list-item-avatar :color="getAvatarColor" :size="size">
    <img
      v-if="email"
      :src="getGravatar"
      :style="{ width: `${size + 2}px`, height: `${size + 2}px` }"
      aria-hidden="true"
    />
    <span class="white--text">{{ getNameInitials }}</span>
  </v-list-item-avatar>
</template>

<script>
import md5 from "md5";
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
    },
    size: {
      type: Number,
      required: false,
      default: 40
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
    getGravatar() {
      if (this.email) {
        const hash = md5(this.email.trim().toLowerCase());
        return `https://www.gravatar.com/avatar/${hash}.jpg?d=blank&s=40`;
      }
      return null;
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
};
</script>

<style lang="scss" scoped>
.v-avatar {
  overflow: unset;

  img {
    position: absolute;
  }
}
</style>
