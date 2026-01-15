<template>
  <section :class="{ section: outlined }">
    <v-row v-if="!hideHeader" class="header justify-space-between">
      <h3 class="title">
        <v-icon color="black" size="small" start> mdi-account </v-icon>
        Individuals
        <v-chip
          pill
          density="comfortable"
          class="ml-2"
          data-cy="individual-counter"
        >
          {{ totalResults }}
        </v-chip>
      </h3>
      <div>
        <recommendations @updateTable="queryIndividuals" />
        <v-btn
          height="34"
          color="secondary"
          class="black--text"
          size="small"
          variant="flat"
          data-cy="individual-add"
          @click.stop="openModal = true"
        >
          Add
        </v-btn>
      </div>
    </v-row>

    <v-row class="actions">
      <search
        class="search-box pa-0 flex-grow-1"
        @search="filterSearch"
        filter-selector
        order-selector
        :order-options="[
          {
            title: 'Last updated',
            value: 'lastModified',
          },
          {
            title: 'Last reviewed',
            value: 'lastReviewed',
          },
          {
            title: 'Created date',
            value: 'createdAt',
          },
          {
            title: 'Name',
            value: 'profile__name',
          },
          {
            title: 'Identities',
            value: 'identitiesCount',
          },
        ]"
        :set-filters="setFilters"
      />
      <v-tooltip
        location="bottom"
        transition="expand-y-transition"
        open-delay="200"
      >
        <template v-slot:activator="{ props }">
          <v-btn
            v-if="!hideHeader"
            density="compact"
            variant="outlined"
            height="34"
            class="mr-4 ml-4 order-2"
            data-cy="merge-button"
            v-bind="props"
            :disabled="disabledMerge"
            @click="mergeSelected(selected)"
          >
            <v-icon size="small" start>mdi-call-merge</v-icon>
            Merge
          </v-btn>
        </template>
        <span>Merge selected</span>
      </v-tooltip>
      <v-tooltip
        location="bottom"
        transition="expand-y-transition"
        open-delay="200"
      >
        <template v-slot:activator="{ props }">
          <v-btn
            v-if="!hideHeader"
            density="compact"
            variant="outlined"
            height="34"
            class="order-3"
            data-cy="delete-button"
            v-bind="props"
            :disabled="disabledActions"
            @click="confirmDelete(selected)"
          >
            <v-icon size="small" start>mdi-delete</v-icon>
            Delete
          </v-btn>
        </template>
        <span>Delete selected</span>
      </v-tooltip>
    </v-row>

    <v-data-table-server
      v-model="selected"
      :headers="headers"
      :items="individuals"
      :expanded="expandedItems"
      v-model:page="page"
      :items-length="totalResults"
      :items-per-page="itemsPerPage"
      :loading="loading"
      :show-select="!hideHeader"
      color="primary"
      item-value="uuid"
      hover
      return-object
      @update:expanded="($event) => (expandedItems = $event)"
    >
      <template
        v-slot:item="{
          item,
          toggleExpand,
          isExpanded,
          isSelected,
          internalItem,
          toggleSelect,
        }"
      >
        <individual-entry
          :draggable="isExpandable"
          :name="item.name"
          :organization="item.organization"
          :email="item.email"
          :username="item.username"
          :sources="item.sources"
          :uuid="item.uuid"
          :is-expanded="isExpanded(internalItem)"
          :is-locked="item.isLocked"
          :is-bot="item.isBot"
          :is-selected="isSelected([internalItem])"
          :is-highlighted="item.uuid === highlightIndividual"
          :is-expandable="isExpandable"
          @dblclick="expandItem(isExpanded, toggleExpand, item, internalItem)"
          @expand="expandItem(isExpanded, toggleExpand, item, internalItem)"
          @edit="updateProfileInfo($event, item.uuid)"
          @saveIndividuals="$emit('saveIndividuals', [item])"
          @dragstart="startDrag(internalItem, isSelected, toggleSelect, $event)"
          @dragend="removeClass(item, $event)"
          @select="toggleSelect(internalItem)"
          @delete="confirmDelete([item])"
          @merge="mergeSelected([item.uuid, ...$event])"
          @move="move($event)"
          @highlight="$emit('highlight', item)"
          @stopHighlight="$emit('stopHighlight', item)"
          @lock="handleLock(item.uuid, $event)"
          @enroll="confirmEnroll(item, $event)"
          @openMatchesModal="openMatchesModal(item.uuid)"
        />
      </template>
      <template v-if="isExpandable" v-slot:expanded-row="{ item }">
        <expanded-individual
          :uuid="item.uuid"
          :gender="item.gender"
          :country="item.country"
          :is-bot="item.isBot"
          :is-locked="item.isLocked"
          :enrollments="item.enrollments"
          :identities="item.identities"
          :get-countries="getCountries"
          @edit="updateProfileInfo($event, item.uuid)"
          @unmerge="unmerge($event)"
          @withdraw="removeAffiliation($event, item.uuid)"
          @updateEnrollment="updateEnrollmentDate"
          @openEnrollmentModal="confirmEnroll(item, $event)"
          @openTeamModal="openTeamModal"
        />
      </template>
      <template v-slot:bottom>
        <div class="d-flex align-center text-center pt-2">
          <v-col cols="8" class="ml-auto">
            <v-pagination
              v-model="page"
              :length="pageCount"
              :total-visible="7"
              density="comfortable"
              @update:modelValue="queryIndividuals($event)"
            ></v-pagination>
          </v-col>
          <v-col cols="2">
            <v-text-field
              :model-value="itemsPerPage"
              class="mr-3"
              density="compact"
              label="Items per page"
              type="number"
              min="1"
              hide-details
              :max="totalResults"
              @update:modelValue="changeItemsPerPage($event)"
            ></v-text-field>
          </v-col>
        </div>
      </template>
      <template v-slot:no-data>
        <v-alert v-if="error" class="text-left" density="compact" type="error">
          {{ error }}
        </v-alert>
        <p v-else-if="Object.keys(filters).length > 0">
          No results matched your search.
        </p>
        <p v-else>No data available</p>
      </template>
    </v-data-table-server>

    <v-dialog v-model="dialog.open" max-width="500px">
      <v-card class="pa-3">
        <v-card-title class="headline">{{ dialog.title }}</v-card-title>
        <v-card-text>
          <p v-if="dialog.text" class="pt-2 pb-2 text-body-2">
            {{ dialog.text }}
          </p>
          <div v-if="dialog.showDates">
            <h6 class="subheader">Enrollment dates (optional)</h6>
            <v-row>
              <v-col cols="6">
                <date-input
                  v-model="dialog.dateFrom"
                  label="Date from"
                  outlined
                />
              </v-col>
              <v-col cols="6">
                <date-input v-model="dialog.dateTo" label="Date to" outlined />
              </v-col>
            </v-row>
          </div>
        </v-card-text>
        <v-card-actions v-if="dialog.action">
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog"> Cancel </v-btn>
          <v-btn
            color="primary"
            id="confirm"
            depressed
            @click.stop="dialog.action"
          >
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog"> OK </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <profile-modal
      v-model:is-open="openModal"
      :add-identity="addIdentity"
      :updateProfile="updateProfile"
      :enroll="enroll"
      :get-countries="getCountries"
      :fetch-organizations="fetchOrganizations"
      :add-organization="addOrganization"
      @updateTable="queryIndividuals"
      @updateOrganizations="$emit('updateOrganizations')"
    />

    <enroll-modal
      v-model:is-open="enrollmentModal.open"
      :title="enrollmentModal.title"
      :text="enrollmentModal.text"
      :organization="enrollmentModal.organization"
      :uuid="enrollmentModal.uuid"
      :enroll="enrollIndividual"
      :fetch-organizations="fetchOrganizations"
      :add-organization="addOrganization"
    />

    <team-enroll-modal
      v-if="teamModal.isOpen"
      v-model:is-open="teamModal.isOpen"
      :organization="teamModal.organization"
      :team="teamModal.team"
      :uuid="teamModal.uuid"
      :enrollments="teamModal.enrollments"
      :enroll="enrollIndividual"
      @updateTable="queryIndividuals"
    />

    <matches-modal
      v-if="matchesModal.open"
      v-model:is-open="matchesModal.open"
      :uuid="matchesModal.uuid"
      :recommend-matches="recommendMatches"
    />

    <v-card class="dragged-item pa-2" color="primary" variant="elevated">
      <v-card-item>
        Moving
        {{ this.selected.length }}
        {{ this.selected.length > 1 ? "individuals" : "individual" }}
      </v-card-item>
    </v-card>
  </section>
</template>

<script>
import {
  mergeIndividuals,
  moveIdentity,
  formatIndividual,
  formatIndividuals,
} from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import IndividualEntry from "./IndividualEntry.vue";
import ExpandedIndividual from "./ExpandedIndividual.vue";
import ProfileModal from "./ProfileModal.vue";
import Search from "./Search.vue";
import EnrollModal from "./EnrollModal.vue";
import TeamEnrollModal from "./TeamEnrollModal.vue";
import Recommendations from "./Recommendations.vue";
import MatchesModal from "./MatchesModal.vue";
import DateInput from "./DateInput.vue";

export default {
  name: "IndividualsTable",
  components: {
    IndividualEntry,
    ExpandedIndividual,
    ProfileModal,
    Search,
    EnrollModal,
    TeamEnrollModal,
    Recommendations,
    MatchesModal,
    DateInput,
  },
  mixins: [enrollMixin],
  props: {
    fetchPage: {
      type: Function,
      required: true,
    },
    deleteItem: {
      type: Function,
      required: true,
    },
    mergeItems: {
      type: Function,
      required: true,
    },
    unmergeItems: {
      type: Function,
      required: true,
    },
    highlightIndividual: {
      type: String,
      required: false,
    },
    moveItem: {
      type: Function,
      required: true,
    },
    addIdentity: {
      type: Function,
      required: true,
    },
    updateProfile: {
      type: Function,
      required: true,
    },
    enroll: {
      type: Function,
      required: true,
    },
    getCountries: {
      type: Function,
      required: true,
    },
    lockIndividual: {
      type: Function,
      required: true,
    },
    unlockIndividual: {
      type: Function,
      required: true,
    },
    updateEnrollment: {
      type: Function,
      required: true,
    },
    withdraw: {
      type: Function,
      required: true,
    },
    setFilters: {
      type: String,
      required: false,
    },
    fetchOrganizations: {
      type: Function,
      required: true,
    },
    recommendMatches: {
      type: Function,
      required: true,
    },
    hideHeader: {
      type: Boolean,
      required: false,
    },
    isExpandable: {
      type: Boolean,
      required: false,
    },
    outlined: {
      type: Boolean,
      required: false,
    },
    expandIndividual: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      filters: {},
      headers: [
        { key: "name", title: "Individual", sortable: false },
        { key: "email", title: "Email", align: "center", sortable: false },
        {
          key: "sources",
          title: "Data sources",
          align: "end",
          sortable: false,
        },
        { key: "actions", sortable: false },
      ],
      individuals: [],
      expandedItems: [],
      pageCount: 0,
      page: 0,
      dialog: {
        open: false,
        title: "",
        text: "",
        action: "",
      },
      openModal: false,
      totalResults: 0,
      itemsPerPage: 10,
      allSelected: false,
      orderBy: null,
      loading: false,
      matchesModal: {
        open: false,
        uuid: "",
      },
      selected: [],
      error: null,
    };
  },
  computed: {
    disabledActions() {
      return (
        this.selected.filter((individual) => !individual.isLocked).length === 0
      );
    },
    disabledMerge() {
      return (
        this.selected.filter((individual) => !individual.isLocked).length < 2
      );
    },
  },
  created() {
    this.queryIndividuals(1);
  },
  methods: {
    async queryIndividuals(
      page = this.page,
      filters = this.filters,
      orderBy = this.orderBy
    ) {
      if (this.disabledSearch) return;
      this.loading = true;
      this.error = null;
      try {
        let response = await this.fetchPage(
          page,
          this.itemsPerPage,
          filters,
          orderBy
        );
        if (response) {
          this.individuals = formatIndividuals(
            response.data.individuals.entities
          );
          this.pageCount = response.data.individuals.pageInfo.numPages;
          this.page = response.data.individuals.pageInfo.page;
          this.totalResults = response.data.individuals.pageInfo.totalResults;
          this.allSelected = false;
          this.$emit("updateIndividuals", this.individuals);
        }
      } catch (error) {
        this.error = this.$getErrorMessage(error);
      } finally {
        this.loading = false;
        this.selected = [];
      }
    },
    startDrag(item, isSelected, toggleSelect, event) {
      if (!isSelected(item)) {
        toggleSelect(item);
      }
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.setData("individuals", JSON.stringify(this.selected));
      const dragImage = document.querySelector(".dragged-item");
      event.dataTransfer.setDragImage(dragImage, 0, 0);
      const lockedIndividuals = this.selected.filter(
        (individual) => individual.isLocked
      );
      if (lockedIndividuals.length === this.selected.length) {
        event.dataTransfer.setData("lockActions", true);
      }
    },
    removeClass(item, event) {
      event.target.classList.remove("dragging");
    },
    selectIndividual(individual) {
      individual.isSelected = !individual.isSelected;
      this.allSelected =
        this.selectedIndividuals.length === this.individuals.length;
    },
    deselectIndividuals() {
      this.individuals.forEach((individual) => (individual.isSelected = false));
      this.allSelected = false;
    },
    async deleteIndividuals(individuals) {
      const response = await Promise.all(
        individuals.map((individual) => this.deleteItem(individual.uuid))
      );
      if (response) {
        this.$logger.debug(
          "Deleted individuals",
          individuals.map((individual) => individual.uuid)
        );
        this.$emit("updateWorkspace", {
          remove: individuals.map((individual) => individual.uuid),
        });
        this.queryIndividuals(this.page);
        this.dialog.open = false;
      }
    },
    confirmDelete(individuals) {
      individuals = individuals.filter((individual) => !individual.isLocked);
      const names = individuals.map((individual) => individual.name).join(", ");
      Object.assign(this.dialog, {
        open: true,
        title: "Delete the selected individuals?",
        text: names,
        action: () => this.deleteIndividuals(individuals),
      });
    },
    async merge(fromUuids, toUuid) {
      try {
        const response = await this.mergeItems(fromUuids, toUuid);
        if (response) {
          this.queryIndividuals(this.page);
          this.dialog.open = false;
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.merge.individual]),
            remove: fromUuids,
          });
          this.$logger.debug("Merged individuals", { fromUuids, toUuid });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error merging individuals: ${error}`, {
          fromUuids,
          toUuid,
        });
      }
    },
    mergeSelected(individuals) {
      if (individuals.length > 1) {
        mergeIndividuals(individuals, this.merge, this.dialog);
      }
    },
    async unmerge(uuids) {
      try {
        const response = await this.unmergeItems(uuids);
        if (response && response.data) {
          const unmergedItems = formatIndividuals(
            response.data.unmergeIdentities.individuals
          );
          this.$emit("saveIndividuals", unmergedItems, true);
          this.$emit("updateWorkspace", {
            update: formatIndividuals(
              response.data.unmergeIdentities.individuals
            ),
          });
          this.queryIndividuals(this.page);
          this.$logger.debug("Unmerged individuals", uuids);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error unmerging individuals ${uuids}: ${error}`);
      }
    },
    move(event) {
      moveIdentity(event.fromUuid, event.toUuid, this.moveAction, this.dialog);
    },
    async moveAction(fromUuid, toUuid) {
      this.dialog.open = false;
      try {
        const response = await this.moveItem(fromUuid, toUuid);
        if (response) {
          this.queryIndividuals(this.page);
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.moveIdentity.individual]),
          });
          this.$logger.debug("Moved identity", { fromUuid, toUuid });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error moving ${fromUuid} to ${toUuid}: ${error}`);
      }
    },
    async updateProfileInfo(data, uuid) {
      try {
        const response = await this.updateProfile(data, uuid);
        if (response && response.data.updateProfile) {
          this.queryIndividuals();
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.updateProfile.individual]),
          });
          this.$logger.debug(`Updated profile ${uuid}`, data);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error updating profile: ${error}`, data);
      }
    },
    async handleLock(uuid, lock) {
      if (lock) {
        try {
          const response = await this.lockIndividual(uuid);
          if (response) {
            this.queryIndividuals();
            this.$logger.debug(`Locked individual ${uuid}`);
          }
        } catch (error) {
          Object.assign(this.dialog, {
            open: true,
            title: "Error",
            text: this.$getErrorMessage(error),
            action: null,
          });
          this.$logger.error(`Error locking individual ${uuid}: ${error}`);
        }
      } else {
        try {
          const response = await this.unlockIndividual(uuid);
          if (response) {
            this.queryIndividuals();
            this.$logger.debug(`Unlocked individual ${uuid}`);
          }
        } catch (error) {
          Object.assign(this.dialog, {
            open: true,
            title: "Error",
            text: this.$getErrorMessage(error),
            action: null,
          });
          this.$logger.error(`Error unlocking individual ${uuid}: ${error}`);
        }
      }
    },
    async removeAffiliation(group, uuid) {
      try {
        const response = await this.withdraw(
          uuid,
          group.name,
          group.fromDate,
          group.toDate,
          group.parentOrg
        );
        if (response && response.data.withdraw) {
          this.queryIndividuals();
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.withdraw.individual]),
          });
          this.$logger.debug("Removed affiliation", { uuid, ...group });
          this.$emit("updateOrganizations");
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error removing affiliation: ${error}`, {
          uuid,
          ...group,
        });
      }
    },
    async updateEnrollmentDate(data) {
      try {
        const response = await this.updateEnrollment(data);
        if (response && response.data.updateEnrollment) {
          this.$emit("updateWorkspace", {
            update: formatIndividuals([
              response.data.updateEnrollment.individual,
            ]),
          });
          this.queryIndividuals();
          this.$logger.debug("Updated enrollment", data);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null,
        });
        this.$logger.error(`Error updating enrollment: ${error}`, data);
      }
    },
    filterSearch(filters, orderBy, inputValue) {
      this.filters = filters;
      this.orderBy = orderBy;
      this.queryIndividuals(1);
      this.$emit("setFilters", inputValue);
    },
    selectAll(value) {
      this.individuals.forEach((individual) => (individual.isSelected = value));
    },
    changeItemsPerPage(value) {
      if (value) {
        clearTimeout(this.timer);

        this.timer = setTimeout(() => {
          this.itemsPerPage = parseInt(value, 10);
          this.queryIndividuals(1);
        }, 500);
      }
    },
    closeDialog() {
      Object.assign(this.dialog, {
        open: false,
        title: "",
        text: "",
        action: "",
        showDates: false,
        dateFrom: null,
        dateTo: null,
      });
    },
    openTeamModal(data) {
      const { organization, uuid, enrollments } = data;
      Object.assign(this.teamModal, {
        isOpen: true,
        team: null,
        organization,
        uuid,
        enrollments,
      });
    },
    openMatchesModal(uuid) {
      Object.assign(this.matchesModal, {
        open: true,
        uuid: uuid,
      });
    },
    async getExpandedIndividual(item) {
      const response = await this.expandIndividual(item.uuid);
      const newData = formatIndividual(response.data.individuals.entities[0]);
      return newData;
    },
    async expandItem(isExpanded, toggleExpand, item, internalItem) {
      if (!isExpanded(internalItem)) {
        const data = await this.getExpandedIndividual(item);
        Object.assign(item, data);
      }
      toggleExpand(internalItem);
    },
  },
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
:deep(.v-data-table__wrapper) {
  overflow-x: hidden;
}

.dragged-item {
  max-width: 300px;
  position: absolute;
  top: -300px;
}

.v-table {
  background-color: #ffffff;
}
</style>
