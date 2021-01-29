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

const avatarMixin = {
  computed: {
    getAvatarColor: function() {
      const charCodes = this.getNameInitials
        .split("")
        .map(char => char.charCodeAt(0))
        .join("");
      const index = charCodes % colors.length;

      return colors[index];
    }
  }
};

export { avatarMixin };
