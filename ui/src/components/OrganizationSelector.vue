<template>
  <v-autocomplete
    v-model="inputValue"
    :items="organizations"
    :search-input.sync="search"
    :label="label"
    item-text="name"
    item-value="name"
    clearable
    dense
    hide-selected
    hide-no-data
    outlined
  ></v-autocomplete>
</template>

<script>
export default {
  name: "OrganizationSelector",
  data() {
    return {
      inputValue: this.value,
      organizations: [],
      search: this.value
    };
  },
  props: {
    value: {
      type: String,
      required: false
    },
    fetchOrganizations: {
      type: Function,
      required: true
    },
    label: {
      type: String,
      required: false,
      default: "Organization"
    }
  },
  methods: {
    async getSelectorItems(value) {
      const response = await this.fetchOrganizations(1, 10, { term: value });
      if (response) {
        this.organizations = response.entities;
      }
    }
  },
  watch: {
    search(value) {
      if (value && value.length > 2) {
        this.getSelectorItems(value);
      }
    },
    value() {
      this.inputValue = this.value;
    },
    inputValue() {
      this.$emit("input", this.inputValue);
    }
  },
  mounted() {
    if (this.value) {
      this.getSelectorItems(this.value);
    }
  }
};
</script>
