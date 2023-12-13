<template>
  <v-autocomplete
    v-model="inputValue"
    :items="organizations"
    :search-input.sync="search"
    :label="label"
    :loading="isLoading"
    item-text="name"
    item-value="name"
    :no-data-text="`No matches for &quot;${search}&quot;`"
    :hide-no-data="!search || isLoading"
    cache-items
    clearable
    dense
    outlined
  >
    <template v-slot:append-item>
      <v-list-item v-if="appendContent" @click="createOrganization">
        <v-list-item-content>
          <v-list-item-title>
            <span class="font-weight-regular">Create</span>
            {{ search }}
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  name: "OrganizationSelector",
  data() {
    return {
      inputValue: this.value,
      organizations: [],
      search: this.value,
      isLoading: false,
    };
  },
  props: {
    value: {
      type: String,
      required: false,
    },
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
        const response = await this.addOrganization(this.search);
        this.organizations.splice(0, 0, {
          name: response.data.addOrganization.organization.name,
        });
        this.inputValue = this.search;
        this.$logger.debug(`Created organization "${this.search}"`);
      } catch (error) {
        this.$logger.error(`Error creating organization: ${error}`);
        this.$emit("error", this.$getErrorMessage(error));
      }
    },
  },
  computed: {
    appendContent() {
      return (
        this.search &&
        !this.organizations.some(
          (org) => org.name.toLowerCase() === this.search.toLowerCase()
        )
      );
    },
  },
  watch: {
    search(value) {
      if (value && value.length > 2) {
        this.isLoading = true;
        this.debounceSearch(value);
      }
    },
    value() {
      this.inputValue = this.value;
    },
    inputValue() {
      this.$emit("input", this.inputValue);
    },
  },
  mounted() {
    this.getSelectorItems(this.value);
  },
};
</script>
