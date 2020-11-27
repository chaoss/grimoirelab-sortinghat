<template>
  <v-hover v-slot="{ hover }">
    <v-combobox
      v-model="value"
      :items="options"
      :error-messages="errorMessage"
      :return-object="false"
      :hide-no-data="!text"
      :search-input.sync="searchInput"
      :class="{
        'search--hover': hover || focused,
        'search--hidden': value.length === 0
      }"
      class="search"
      append-outer-icon="mdi-magnify"
      placeholder="Search or filter results"
      clearable
      hide-selected
      multiple
      dense
      small-chips
      @keydown.enter="handleEnter"
      @change="onFilterChange"
      @update:search-input="onFilterChange"
      @click:append-outer="$emit('search', searchFilters)"
      @click:clear="clear"
      @focus="focused = true"
      @blur="focused = false"
    >
      <template v-slot:item="{ item, on }">
        <v-list-item v-on="on">
          <v-list-item-content>
            <v-list-item-title>
              {{ item.text }}
            </v-list-item-title>
          </v-list-item-content>
          <v-list-item-action>
            <v-chip small>
              {{ item.value }}
            </v-chip>
          </v-list-item-action>
        </v-list-item>
      </template>

      <template v-slot:no-data>
        <v-list-item>
          <v-list-item-content>
            <v-list-item-title>
              {{ text }}
            </v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-combobox>
  </v-hover>
</template>

<script>
export default {
  name: "Search",
  data() {
    return {
      searchFilters: {},
      filters: [
        { value: "term", text: "Term" },
        { value: "lastUpdated", text: "Last updated" }
      ],
      lastUpdated: [
        { value: "<", text: "before" },
        { value: "<=", text: "before and including" },
        { value: ">", text: "after" },
        { value: ">=", text: "after and including" },
        { value: "range", text: "range" }
      ],
      options: [],
      value: [],
      searchInput: null,
      text: "",
      errorMessage: "",
      focused: false
    };
  },
  methods: {
    onFilterChange() {
      const lastTerm = this.value[this.value.length - 1];
      switch (lastTerm) {
        case "term":
          this.options = [];
          this.text = "Enter a search term";
          break;
        case "lastUpdated":
          this.options = this.lastUpdated;
          break;
        case "<":
        case "<=":
        case ">=":
        case ">":
          this.options = [];
          this.text = "Enter a YYYY-MM-DD date";
          break;
        case "range":
          this.options = [];
          this.text = "YYYY-MM-DD..YYYY-MM-DD format";
          break;
        default:
          this.options = this.filters;
          this.text = "";
      }
      this.parseSearchValues();
    },
    parseSearchValues() {
      const hasFilters = this.value.some(value =>
        this.filters.some(filter => filter.value === value)
      );

      if (this.value[0] && !hasFilters) {
        this.value.unshift("term");
      }

      Object.assign(this.searchFilters, {
        term: this.parseTerm(),
        lastUpdated: this.parseLastUpdated()
      });
    },
    parseTerm() {
      const termIndex = this.value.findIndex(value => value === "term");
      let value;

      if (termIndex !== -1) {
        value = this.value[termIndex + 1]
          ? this.value[termIndex + 1].trim()
          : undefined;
      }

      return value;
    },
    parseLastUpdated() {
      const lastUpdatedIndex = this.value.findIndex(
        value => value === "lastUpdated"
      );
      let result;

      if (lastUpdatedIndex !== -1) {
        const operator = this.value[lastUpdatedIndex + 1];
        const validOperator = this.lastUpdated.some(
          valid => valid.value === operator
        );
        const value = this.value[lastUpdatedIndex + 2];

        if (operator && !validOperator) {
          this.errorMessage = "Invalid operator";
          return;
        }

        if (operator === "range" && value) {
          try {
            const dates = value.split("..");
            if (dates.length !== 2 || dates[0] > dates[1]) throw new Error();
            result = dates.map(date => new Date(date).toISOString()).join("..");
            this.errorMessage = "";
          } catch {
            this.errorMessage = "Invalid date";
          }
        } else if (value) {
          try {
            const date = new Date(value).toISOString();
            result = `${operator}${date}`;
            this.errorMessage = "";
          } catch {
            this.errorMessage = "Invalid date";
          }
        }
      } else {
        this.errorMessage = "";
      }
      return result;
    },
    clear() {
      Object.keys(this.searchFilters).forEach(key =>
        this.$set(this.searchFilters, key, undefined)
      );
      this.value = [];
      this.errorMessage = "";
      this.$emit("search", this.searchFilters);
    },
    handleEnter() {
      if (!this.searchInput) {
        this.$emit("search", this.searchFilters);
      }
    }
  },
  created() {
    this.options = this.filters;
  }
};
</script>
<style lang="scss">
.search {
  width: 400px;

  &--hidden {
    width: 33px;
    transition: width 0.5s;

    ::v-deep .v-text-field__details {
      max-width: 0;
      height: 14px;
    }
    .v-menu__content {
      display: none;
    }
  }

  &--hover {
    width: 400px;
  }

  .v-input__icon--append {
    display: none;
  }
}
</style>
