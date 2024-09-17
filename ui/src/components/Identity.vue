<template>
  <v-row class="d-flex align-center flex-nowrap" no-gutters>
    <v-col class="uuid d-flex align-center">
      <v-chip
        class="text-center pr-2"
        :class="{ 'v-chip--border': isMain }"
        :variant="isMain ? 'tonal' : 'outlined'"
      >
        <span class="clip mr-1">{{ uuid }}</span>
        <span v-if="isMain" class="d-sr-only"> Main identity </span>
        <v-tooltip open-delay="100" location="bottom">
          <template v-slot:activator="{ props }">
            <v-btn
              v-bind="props"
              density="comfortable"
              icon="mdi-content-copy"
              size="small"
              variant="text"
              @click="copy(uuid)"
              @mouseenter="resetCopyText"
            />
          </template>
          <span>{{ tooltip }}</span>
        </v-tooltip>
      </v-chip>
    </v-col>
    <v-col class="ma-2" md="2">
      <span>{{ name }}</span>
    </v-col>
    <v-col class="ma-2" cols="3">
      <span class="text-break">{{ email }}</span>
    </v-col>
    <v-col class="ma-2">
      <a
        v-if="source?.toLowerCase() === 'github'"
        :href="`http://github.com/${username}`"
        class="link--underline font-weight-regular"
        target="_blank"
      >
        {{ username }}
        <v-icon size="x-small" end>mdi-open-in-new</v-icon>
      </a>
      <a
        v-else-if="source?.toLowerCase() === 'linkedin'"
        :href="`https://www.linkedin.com/in/${username}`"
        class="link--underline font-weight-regular"
        target="_blank"
      >
        {{ username }}
        <v-icon size="x-small" end>mdi-open-in-new</v-icon>
      </a>
      <span v-else class="text-break">{{ username }}</span>
    </v-col>
    <v-col class="ma-2" v-if="source !== null">
      <span>{{ source }}</span>
    </v-col>
  </v-row>
</template>

<script>
const defaultCopyText = "Copy full UUID";
const successCopyText = "Copied";

export default {
  name: "identity",
  props: {
    uuid: {
      type: String,
      required: true,
    },
    name: {
      type: String,
      required: false,
    },
    email: {
      type: String,
      required: false,
    },
    username: {
      type: String,
      required: false,
    },
    source: {
      type: String,
      required: false,
      default: null,
    },
    isMain: {
      type: Boolean,
      required: false,
    },
  },
  data: () => ({
    tooltip: defaultCopyText,
  }),
  methods: {
    copy(text) {
      navigator.clipboard.writeText(text).then(() => {
        this.tooltip = successCopyText;
      });
    },
    resetCopyText() {
      this.tooltip = defaultCopyText;
    },
  },
};
</script>
<style lang="scss" scoped>
.clip {
  max-width: 7ch;
  overflow: hidden;
  text-overflow: clip;
  font-family: monospace;
}

.v-tooltip__content {
  font-size: 12px;
}

:deep(.v-chip--variant-tonal) .v-chip__underlay {
  opacity: 0.04;
}
</style>
