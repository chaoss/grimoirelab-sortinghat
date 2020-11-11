<template>
  <v-row no-gutters>
    <v-col class="uuid">
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-chip class="text-center clip" v-on="on" outlined tile>
            {{ uuid }}
          </v-chip>
        </template>
        <span>{{ uuid }}</span>
      </v-tooltip>
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
      required: false
    },
    email: {
      type: String,
      required: false
    },
    username: {
      type: String,
      required: false
    },
    source: {
      type: String,
      required: false,
      default: null
    }
  }
};
</script>
<style lang="scss" scoped>
.clip ::v-deep .v-chip__content {
  max-width: 7ch;
  overflow: hidden;
  text-overflow: clip;
  font-family: monospace;
}

.v-tooltip__content {
  font-size: 12px;
}
</style>
