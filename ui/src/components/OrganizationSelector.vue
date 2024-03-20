<template>
  <v-autocomplete
    v-model="inputValue"
    :items="organizations"
    :label="label"
    :loading="isLoading"
    :filter="filterItems"
    :no-data-text="`No matches for &quot;${searchValue}&quot;`"
    :hide-no-data="isLoading"
    item-title="name"
    item-value="name"
    variant="outlined"
    density="comfortable"
    clearable
    @update:search="search"
  >
    <template v-slot:append-item>
      <v-list-item v-if="appendContent" @click="createOrganization">
        <v-list-item-title>
          <span class="font-weight-regular">Create</span>
          {{ searchValue }}
        </v-list-item-title>
      </v-list-item>
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  name: "OrganizationSelector",
  data() {
    return {
      inputValue: "",
      organizations: [],
      isLoading: false,
      searchValue: null,
    };
  },
  emits: ["update:modelValue"],
  props: {
    addOrganization: {
      type: Function,
      required: true,
    },
    fetchOrganizations: {
      type: Function,
      required: true,
    },
    label: {
      type: String,
      required: false,
      default: "Organization",
    },
  },
  methods: {
    debounceSearch(searchValue) {
      clearTimeout(this.timer);

      this.timer = setTimeout(() => {
        this.getSelectorItems(searchValue);
      }, 500);
    },
    async getSelectorItems(value) {
      const filters = value ? { term: value } : {};
      const response = await this.fetchOrganizations(1, 10, filters);
      if (response) {
        this.organizations = response.entities;
        this.isLoading = false;
      }
    },
    async createOrganization() {
      try {
        const response = await this.addOrganization(this.searchValue);
        const newOrg = {
          name: response.data.addOrganization.organization.name,
        };
        this.organizations = [newOrg, ...this.organizations];
        this.inputValue = this.searchValue;
        this.$logger.debug(`Created organization "${this.searchValue}"`);
      } catch (error) {
        this.$logger.error(`Error creating organization: ${error}`);
        this.$emit("error", this.$getErrorMessage(error));
      }
    },
    filterItems(item) {
      // Return all items because the query is already filtered
      return item;
    },
    search(value) {
      this.searchValue = value;
      if (!value || (value.length > 2 && value !== this.inputValue)) {
        this.isLoading = true;
        this.debounceSearch(value);
      }
    },
  },
  computed: {
    appendContent() {
      return (
        this.searchValue &&
        !this.organizations.some(
          (org) =>
            org.name.toLowerCase() === this.searchValue.toLowerCase() ||
            org.aliases.some(
              (alias) =>
                alias.alias.toLowerCase() === this.searchValue.toLowerCase()
            )
        )
      );
    },
  },
  watch: {
    inputValue() {
      this.$emit("update:modelValue", this.inputValue);
    },
  },
  mounted() {
    this.getSelectorItems(this.value);
  },
};
</script>
