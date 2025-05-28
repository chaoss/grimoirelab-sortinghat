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
        on {{ $formatDate(item.createdAt, "YYYY-MM-DD") }}
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
      const name = item.name.split("-")[0];

      switch (name) {
        case "add_identity": {
          const operation = item.operations?.find(
            (op) => op.entityType === "identity"
          );
          const source = operation.args.source;
          const uuid = operation.args.uuid?.substring(0, 7);
          return `added ${source} identity ${uuid}`;
        }
        case "enroll": {
          const organization = item.operations[0]?.args.group;
          return `enrolled individual in ${organization}`;
        }
        case "lock":
          return "locked the profile";
        case "merge": {
          const uuids = item.operations
            .filter((op) => op.args.identity)
            .map((op) => op.args.identity.substring(0, 7));
          return `merged ${
            uuids.length > 1 ? "identities" : "identity"
          } ${uuids.join(", ")}`;
        }
        case "merge_organizations": {
          const operation = item.operations?.find(
            (op) => op.entityType === "alias"
          );
          return `merged ${operation.args.name} into ${operation.args.organization}`;
        }
        case "review":
          return "reviewed the profile";
        case "unlock":
          return "unlocked the profile";
        case "unmerge_identities":
          return "split identity";
        case "update_profile": {
          const fields = Object.keys(item.operations[0]?.args)
            .filter((key) => key !== "individual")
            .join(", ");
          return `updated profile ${fields}`;
        }
        case "withdraw": {
          const organization = item.operations[0]?.args.group;
          return `withdrew individual from ${organization}`;
        }
        default:
          return name.replace("-", " ");
      }
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
