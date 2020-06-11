<template>
  <v-card class="mx-auto" raised>
    <v-list-item class="grow">
      <v-list-item-avatar color="grey">
        {{ getNameInitials }}
      </v-list-item-avatar>

      <v-list-item-content>
        <v-list-item-title>{{ name }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <slot />
  </v-card>
</template>

<script>
export default {
  name: "individualcard",
  props: {
    name: {
      type: String,
      required: true
    }
  },
  computed: {
    getNameInitials: function() {
      var names = this.name.split(" ");
      var initials = names[0].substring(0, 1).toUpperCase();

      if (names.length > 1) {
        initials += names[names.length - 1].substring(0, 1).toUpperCase();
      }

      return initials;
    }
  }
};
</script>
