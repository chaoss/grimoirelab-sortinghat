<template>
  <tr
    :class="{ dropzone: dropZone }"
    @drop.stop="onDrop($event)"
    @dragover.prevent="isDropZone($event, true)"
    @dragenter.prevent="isDropZone($event, true)"
    @dragleave.prevent="isDropZone($event, false)"
  >
    <td class="font-weight-medium pl-8">
      <router-link
        :to="{
          name: 'Organization',
          params: { name: encodeURIComponent(name) },
        }"
        target="_blank"
        class="link--underline"
      >
        {{ name }}
      </router-link>
    </td>
    <td class="text-right text--secondary">
      <v-tooltip
        location="bottom"
        transition="expand-y-transition"
        open-delay="200"
      >
        <template v-slot:activator="{ props }">
          <v-btn
            variant="flat"
            size="default"
            color="transparent"
            v-bind="props"
            @click.stop="$emit('getEnrollments')"
          >
            {{ enrollments }}
            <v-icon end> mdi-account-multiple </v-icon>
          </v-btn>
        </template>
        <span>Enrollments</span>
      </v-tooltip>
    </td>
    <td class="text-right">
      <v-menu v-model="showMenu" location="left" nudge-left="16">
        <template v-slot:activator="{ props }">
          <v-btn
            icon="mdi-dots-vertical"
            density="comfortable"
            size="small"
            variant="text"
            v-bind="props"
          >
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item @click="$emit('edit')">
            <v-list-item-title> Edit domains and aliases </v-list-item-title>
          </v-list-item>
          <v-menu v-model="showTeamMenu" :close-on-content-click="false">
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props">
                <v-list-item-title>Add a team</v-list-item-title>
              </v-list-item>
            </template>
            <v-card min-width="200">
              <v-card-text>
                <v-text-field
                  v-model="newTeam"
                  label="Team name"
                  color="primary"
                  density="compact"
                  hide-details
                  single-line
                />
              </v-card-text>
              <v-card-actions>
                <v-btn
                  @click="
                    showTeamMenu = false;
                    newTeam = '';
                  "
                >
                  Cancel
                </v-btn>
                <v-btn
                  @click="
                    $emit('addTeam', newTeam);
                    showTeamMenu = false;
                    newTeam = '';
                  "
                >
                  Save
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-menu>
          <v-list-item @click="$emit('delete')">
            <v-list-item-title>Delete organization</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      <v-btn
        :icon="isExpanded ? 'mdi-chevron-up' : 'mdi-chevron-down'"
        density="comfortable"
        size="small"
        variant="text"
        @click.stop="$emit('expand')"
      >
      </v-btn>
    </td>
  </tr>
</template>

<script>
export default {
  name: "OrganizationEntry",
  props: {
    name: {
      type: String,
      required: true,
    },
    enrollments: {
      type: Number,
      required: true,
    },
    isExpanded: {
      type: Boolean,
      required: true,
    },
    isEditable: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      dropZone: false,
      showMenu: false,
      showTeamMenu: false,
      newTeam: "",
    };
  },
  methods: {
    onDrop(event) {
      this.dropZone = false;
      const organization = event.dataTransfer.getData("group");
      const isTeam = event.dataTransfer.types.includes("parentorg");
      const individuals = event.dataTransfer.getData("individuals");

      if (organization && organization !== this.name && !isTeam) {
        this.$emit("merge:orgs", {
          fromOrg: organization,
          toOrg: this.name,
        });
      } else if (individuals) {
        const droppedIndividuals = JSON.parse(individuals).filter(
          (individual) => !individual.isLocked
        );
        if (droppedIndividuals.length > 0) {
          this.$emit("enroll", {
            individuals: droppedIndividuals,
            group: this.name,
          });
        }
      }
    },
    isDropZone(event, isDragging) {
      const types = event.dataTransfer.types;
      this.dropZone =
        isDragging &&
        !types.includes("lockactions") &&
        !types.includes("parentorg");
    },
  },
};
</script>
<style lang="scss" scoped>
@use "../styles/index.scss";
tr {
  cursor: pointer;
}

td:last-of-type {
  width: 100px;
}

tr[draggable="true"] {
  td:first-of-type {
    position: relative;

    &::before {
      font: normal normal normal 24px/1 "Material Design Icons";
      font-size: 1rem;
      content: "\F01DD";
      color: rgba(0, 0, 0, 0.62);
      position: absolute;
      left: 4px;
      top: 30%;
      opacity: 0;
      cursor: grab;
    }
  }

  &:hover td::before {
    opacity: 1;
  }
}
</style>
