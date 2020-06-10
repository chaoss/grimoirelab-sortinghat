<template>
  <v-row no-gutters>
    <v-col cols="2">
      <v-chip class="text-center" outlined tile>
        {{ uuid }}
      </v-chip>
    </v-col>
    <v-col class="ma-2 text-center">
      <span>{{ name }}</span>
    </v-col>
    <v-col class="ma-2 text-center">
      <span>{{ email }}</span>
    </v-col>
    <v-col class="ma-2 text-center">
      <span>{{ username }}</span>
    </v-col>
    <v-col class="ma-2 text-center" v-if="source !== null">
      <span>{{ source }}</span>
    </v-col>
  </v-row>
</template>

<script>
export default {
  name: "identity",
  props: {
    uuid: {
      type: String,
      required: true
    },
    name: {
      type: String,
      required: true
    },
    email: {
      type: String,
      required: true
    },
    username: {
      type: String,
      required: true
    },
    source: {
      type: String,
      required: false,
      default: null
    }
  }
};
</script>
