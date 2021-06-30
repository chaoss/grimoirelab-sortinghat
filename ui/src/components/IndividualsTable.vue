<template>
  <section class="section">
    <v-row class="header">
      <h3 class="title">
        <v-icon color="black" left dense>
          mdi-account-multiple
        </v-icon>
        Individuals
        <v-chip pill small class="ml-2">{{ totalResults }}</v-chip>
      </h3>
      <v-btn
        depressed
        small
        height="34"
        color="secondary"
        class="black--text"
        @click.stop="openModal = true"
      >
        Add
      </v-btn>
    </v-row>

    <v-row class="actions">
      <v-checkbox
        v-model="allSelected"
        value
        class="mt-0"
        :indeterminate="isIndeterminate"
        :label="
          selectedIndividuals.length === 0
            ? 'Select all'
            : `${selectedIndividuals.length} selected`
        "
        @change="selectAll($event)"
      >
      </v-checkbox>
      <search
        class="ml-auto pa-0 flex-grow-0"
        @search="filterSearch"
        filter-selector
        order-selector
        :order-options="[
          {
            text: 'Last updated',
            value: 'lastModified'
          },
          {
            text: 'Created date',
            value: 'createdAt'
          },
          {
            text: 'Name',
            value: 'profile__name'
          }
        ]"
        :set-filters="setFilters"
      />
      <v-tooltip bottom transition="expand-y-transition" open-delay="200">
        <template v-slot:activator="{ on }">
          <v-btn
            text
            small
            outlined
            height="34"
            class="mr-4 ml-2"
            v-on="on"
            :disabled="disabledMerge"
            @click="mergeSelected(selectedIndividuals)"
          >
            <v-icon small left>mdi-call-merge</v-icon>
            Merge
          </v-btn>
        </template>
        <span>Merge selected</span>
      </v-tooltip>
      <v-tooltip bottom transition="expand-y-transition" open-delay="200">
        <template v-slot:activator="{ on }">
          <v-btn
            text
            small
            outlined
            height="34"
            v-on="on"
            :disabled="disabledActions"
            @click="confirmDelete(selectedIndividuals)"
          >
            <v-icon small left>mdi-delete</v-icon>
            Delete
          </v-btn>
        </template>
        <span>Delete selected</span>
      </v-tooltip>
    </v-row>

    <v-data-table
      hide-default-header
      hide-default-footer
      :headers="headers"
      :items="individuals"
      :expanded.sync="expandedItems"
      item-key="uuid"
      :page.sync="page"
      :items-per-page="itemsPerPage"
    >
      <template v-slot:item="{ item, expand, isExpanded }">
        <individual-entry
          draggable
          :name="item.name"
          :organization="item.organization"
          :email="item.email"
          :username="item.username"
          :sources="item.sources"
          :uuid="item.uuid"
          :is-expanded="isExpanded"
          :is-locked="item.isLocked"
          :is-bot="item.isBot"
          :is-selected="item.isSelected"
          :is-highlighted="item.uuid === highlightIndividual"
          @dblclick.native="expand(!isExpanded)"
          @expand="expand(!isExpanded)"
          @edit="updateProfileInfo($event, item.uuid)"
          @saveIndividual="$emit('saveIndividual', item)"
          @dragstart.native="startDrag(item, $event)"
          @dragend.native="removeClass(item, $event)"
          @select="selectIndividual(item)"
          @delete="confirmDelete([item])"
          @merge="mergeSelected([item.uuid, ...$event])"
          @move="move($event)"
          @highlight="$emit('highlight', item)"
          @stopHighlight="$emit('stopHighlight', item)"
          @lock="handleLock(item.uuid, $event)"
          @enroll="confirmEnroll(item.uuid, $event)"
        />
      </template>
      <template v-slot:expanded-item="{ item }">
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
        />
      </template>
    </v-data-table>

    <div class="d-flex align-baseline text-center pt-2">
      <v-col cols="8" class="ml-auto">
        <v-pagination
          v-model="page"
          :length="pageCount"
          :total-visible="7"
          @input="queryIndividuals($event)"
        ></v-pagination>
      </v-col>
      <v-col cols="2">
        <v-text-field
          :value="itemsPerPage"
          class="mr-3"
          label="Items per page"
          type="number"
          min="1"
          :max="totalResults"
          @change="changeItemsPerPage($event)"
        ></v-text-field>
      </v-col>
    </div>

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
          <v-btn text @click="closeDialog">
            Cancel
          </v-btn>
          <v-btn color="primary" depressed @click.stop="dialog.action">
            Confirm
          </v-btn>
        </v-card-actions>
        <v-card-actions v-else>
          <v-spacer></v-spacer>
          <v-btn text color="primary" @click="closeDialog">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <profile-modal
      :is-open.sync="openModal"
      :add-identity="addIdentity"
      :updateProfile="updateProfile"
      :enroll="enroll"
      :get-countries="getCountries"
      @updateTable="queryIndividuals"
    />

    <v-card class="dragged-item" color="primary" dark>
      <v-card-subtitle>
        Moving
        {{ this.selectedIndividuals.length }}
        {{ this.selectedIndividuals.length > 1 ? "individuals" : "individual" }}
      </v-card-subtitle>
    </v-card>
  </section>
</template>

<script>
import {
  mergeIndividuals,
  moveIdentity,
  formatIndividuals
} from "../utils/actions";
import { enrollMixin } from "../mixins/enroll";
import IndividualEntry from "./IndividualEntry.vue";
import ExpandedIndividual from "./ExpandedIndividual.vue";
import ProfileModal from "./ProfileModal.vue";
import Search from "./Search.vue";

export default {
  name: "IndividualsTable",
  components: {
    IndividualEntry,
    ExpandedIndividual,
    ProfileModal,
    Search
  },
  mixins: [enrollMixin],
  props: {
    fetchPage: {
      type: Function,
      required: true
    },
    deleteItem: {
      type: Function,
      required: true
    },
    mergeItems: {
      type: Function,
      required: true
    },
    unmergeItems: {
      type: Function,
      required: true
    },
    highlightIndividual: {
      type: String,
      required: false
    },
    moveItem: {
      type: Function,
      required: true
    },
    addIdentity: {
      type: Function,
      required: true
    },
    updateProfile: {
      type: Function,
      required: true
    },
    enroll: {
      type: Function,
      required: true
    },
    getCountries: {
      type: Function,
      required: true
    },
    lockIndividual: {
      type: Function,
      required: true
    },
    unlockIndividual: {
      type: Function,
      required: true
    },
    updateEnrollment: {
      type: Function,
      required: true
    },
    withdraw: {
      type: Function,
      required: true
    },
    setFilters: {
      type: String,
      required: false
    }
  },
  data() {
    return {
      filters: {},
      headers: [
        { value: "name" },
        { value: "email" },
        { value: "sources" },
        { value: "actions" }
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
        showDates: false,
        dateFrom: null,
        dateTo: null
      },
      openModal: false,
      totalResults: 0,
      itemsPerPage: 10,
      allSelected: false,
      orderBy: null
    };
  },
  computed: {
    disabledActions() {
      return (
        this.selectedIndividuals.filter(individual => !individual.isLocked)
          .length === 0
      );
    },
    disabledMerge() {
      return (
        this.selectedIndividuals.filter(individual => !individual.isLocked)
          .length < 2
      );
    },
    selectedIndividuals() {
      return this.individuals.filter(individual => individual.isSelected);
    },
    isIndeterminate() {
      return (
        this.selectedIndividuals.length < this.individuals.length &&
        this.selectedIndividuals.length !== 0
      );
    }
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
    },
    startDrag(item, event) {
      item.isSelected = true;
      event.dataTransfer.dropEffect = "move";
      event.dataTransfer.setData(
        "individuals",
        JSON.stringify(this.selectedIndividuals)
      );
      const dragImage = document.querySelector(".dragged-item");
      event.dataTransfer.setDragImage(dragImage, 0, 0);
      const lockedIndividuals = this.selectedIndividuals.filter(
        individual => individual.isLocked
      );
      if (lockedIndividuals.length === this.selectedIndividuals.length) {
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
      this.individuals.forEach(individual => (individual.isSelected = false));
      this.allSelected = false;
    },
    async deleteIndividuals(individuals) {
      const response = await Promise.all(
        individuals.map(individual => this.deleteItem(individual.uuid))
      );
      if (response) {
        this.$logger.debug(
          "Deleted individuals",
          individuals.map(individual => individual.uuid)
        );
        this.queryIndividuals(this.page);
        this.dialog.open = false;
      }
    },
    confirmDelete(individuals) {
      individuals = individuals.filter(individual => !individual.isLocked);
      const names = individuals.map(individual => individual.name).join(", ");
      Object.assign(this.dialog, {
        open: true,
        title: "Delete the selected items?",
        text: names,
        action: () => this.deleteIndividuals(individuals)
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
            remove: fromUuids
          });
          this.$logger.debug("Merged individuals", { fromUuids, toUuid });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(`Error merging individuals: ${error}`, {
          fromUuids,
          toUuid
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
          this.$emit("saveIndividual", unmergedItems[0]);
          this.queryIndividuals(this.page);
          this.$logger.debug("Unmerged individuals", uuids);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
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
            update: formatIndividuals([response.data.moveIdentity.individual])
          });
          this.$logger.debug("Moved identity", { fromUuid, toUuid });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
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
            update: formatIndividuals([response.data.updateProfile.individual])
          });
          this.$logger.debug(`Updated profile ${uuid}`, data);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
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
            action: null
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
            action: null
          });
          this.$logger.error(`Error unlocking individual ${uuid}: ${error}`);
        }
      }
    },
    async removeAffiliation(organization, uuid) {
      try {
        const response = await this.withdraw(
          uuid,
          organization.name,
          organization.fromDate,
          organization.toDate
        );
        if (response && response.data.withdraw) {
          this.queryIndividuals();
          this.$emit("updateWorkspace", {
            update: formatIndividuals([response.data.withdraw.individual])
          });
          this.$logger.debug("Removed affiliation", { uuid, ...organization });
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(`Error removing affiliation: ${error}`, {
          uuid,
          ...organization
        });
      }
    },
    async updateEnrollmentDate(data) {
      try {
        const response = await this.updateEnrollment(data);
        if (response && response.data.updateEnrollment) {
          this.$emit("updateWorkspace", {
            update: formatIndividuals([
              response.data.updateEnrollment.individual
            ])
          });
          this.queryIndividuals();
          this.$logger.debug("Updated enrollment", data);
        }
      } catch (error) {
        Object.assign(this.dialog, {
          open: true,
          title: "Error",
          text: this.$getErrorMessage(error),
          action: null
        });
        this.$logger.error(`Error updating enrollment: ${error}`, data);
      }
    },
    filterSearch(filters, orderBy) {
      this.filters = filters;
      this.orderBy = orderBy;
      this.queryIndividuals(1);
    },
    selectAll(value) {
      this.individuals.forEach(individual => (individual.isSelected = value));
    },
    changeItemsPerPage(value) {
      if (value) {
        this.itemsPerPage = parseInt(value, 10);
        this.queryIndividuals(1);
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
        dateTo: null
      });
    }
  }
};
</script>
<style lang="scss" scoped>
@import "../styles/index.scss";
::v-deep .v-data-table__wrapper {
  overflow-x: hidden;
}
.actions {
  ::v-deep .v-label {
    font-size: 0.9rem;
  }

  ::v-deep .v-input--checkbox {
    padding-top: 6px;
    margin-left: -1px;
  }
}
.dragged-item {
  max-width: 300px;
  position: absolute;
  top: -300px;
}
</style>
