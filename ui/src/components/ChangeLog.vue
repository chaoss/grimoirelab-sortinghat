<template>
  <div class="fit-content">
    <v-list-subheader class="text-subtitle-2 mb-2"> Activity </v-list-subheader>
    <v-timeline v-if="changes.length > 0" side="end">
      <v-timeline-item
        v-for="item in changes"
        :key="item.tuid"
        dot-color="on-surface-variant"
        size="x-small"
        line-thickness="1"
      >
        <span class="font-weight-medium">
          {{
            item.name.includes("-") ? "An automated process" : item.authoredBy
          }}
        </span>
        {{ parseText(item) }}
      </v-timeline-item>
    </v-timeline>
    <p v-else class="v-timeline">No recent activity for this profile</p>
  </div>
</template>
<script>
export default {
  props: {
    changes: {
      type: Array,
      required: true,
    },
  },
  methods: {
    parseText(item) {
      const actions = {
        add_identity: "added an identity",
        enroll: "added an organization",
        lock: "locked the profile",
        merge: "merged identities",
        unmerge_identities: "split identities",
        unlock: "unlocked the profile",
        update_profile: "updated profile data",
        withdraw: "removed an organization",
        review: "reviewed the profile",
      };
      const name = item.name.split("-")[0];

      const action = actions[name] || name.replace("-", " ");
      const date = this.$formatDate(item.createdAt, "YYYY-MM-DD");

      return `${action} on ${date}`;
    },
  },
};
</script>
<style lang="scss">
.fit-content {
  width: fit-content;
}

.v-timeline {
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface-variant));
}

.v-timeline-divider__dot--size-x-small {
  height: 12px;
  width: 12px;
}

.v-timeline--vertical .v-timeline-item:last-child .v-timeline-divider__after {
  height: 0;
}

.v-timeline--vertical.v-timeline.v-timeline--side-end
  .v-timeline-item
  .v-timeline-item__opposite {
  padding-inline-end: 20px;
}
</style>
