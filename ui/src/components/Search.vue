<template>
  <v-text-field
    v-model.trim="inputValue"
    append-outer-icon="mdi-magnify"
    class="search pa-0 flex-grow-0"
    :error-messages="errorMessage"
    clearable
    label="Search"
    type="text"
    height="30"
    hint=" "
    persistent-hint
    single-line
    outlined
    dense
    @click:append-outer="search"
    @click:clear="clear"
    @keyup.enter="search"
    @focus="isFocused = true"
    @blur="isFocused = false"
  >
    <template v-slot:prepend v-if="filterSelector">
      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            class="text-body-1"
            depressed
            color="white"
            height="30"
            v-bind="attrs"
            v-on="on"
          >
            Filters
            <v-icon small right>mdi-menu-down</v-icon>
          </v-btn>
        </template>
        <v-list dense class="mt-1">
          <v-list-item
            v-for="(item, i) in validFilters"
            :key="i"
            @click="setFilter(item)"
          >
            <v-list-item-title>
              {{ item.filter }}
            </v-list-item-title>
          </v-list-item>
          <v-divider />
          <v-list-item href="/search-help" target="_blank">
            <v-list-item-title>
              <v-icon small left>mdi-open-in-new</v-icon>
              View search syntax
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-text-field>
</template>

<script>
export default {
  name: "Search",
  props: {
    filterSelector: {
      type: Boolean,
      required: false,
      default: false
    },
    validFilters: {
      type: Array,
      required: false,
      default: () => [
        {
          filter: "country",
          type: "string"
        },
        {
          filter: "isBot",
          type: "boolean"
        },
        {
          filter: "isLocked",
          type: "boolean"
        },
        {
          filter: "gender",
          type: "string"
        },
        {
          filter: "lastUpdated",
          type: "string"
        },
        {
          filter: "source",
          type: "string"
        }
      ]
    }
  },
  data() {
    return {
      inputValue: "",
      filters: {},
      isFocused: false,
      errorMessage: undefined,
      dialog: false
    };
  },
  methods: {
    search() {
      this.parseFilters();
      if (this.errorMessage) return;
      this.$emit("search", this.filters);
    },
    parseFilters() {
      const terms = [];
      this.filters = {};
      this.errorMessage = undefined;

      if (!this.inputValue) return;

      const input = this.parseQuotes(this.inputValue);
      input.split(" ").forEach(value => {
        if (value.includes(":")) {
          const [filter, text] = value.split(":");
          if (
            this.validFilters.length === 0 ||
            !this.validFilters.find(vfilter => vfilter.filter === filter)
          ) {
            this.errorMessage = `Invalid filter "${filter}"`;
          } else if (filter === "lastUpdated") {
            this.parseLastUpdated(text);
          } else if (this.isBooleanFilter(filter)) {
            this.parseBooleanFilter(filter, text);
          } else {
            this.filters[filter] = text;
          }
        } else {
          terms.push(value);
        }
      });

      if (terms.length > 0) {
        this.filters.term = terms.join(" ").trim();
      }
    },
    parseLastUpdated(inputValue) {
      const operator = ["<=", ">=", "<", ">", ".."].find(value =>
        inputValue.includes(value)
      );

      if (!operator) {
        return (this.errorMessage = "Invalid operator");
      }

      const values = inputValue.replace(operator, ` ${operator} `).split(" ");

      try {
        this.filters.lastUpdated = values
          .map(value => {
            if (value) {
              return value === operator
                ? operator
                : new Date(value).toISOString();
            }
          })
          .join("");
      } catch (error) {
        this.errorMessage = "Invalid date";
      }
    },
    parseBooleanFilter(filter, value) {
      if (value === "true") {
        this.filters[filter] = true;
      } else if (value === "false") {
        this.filters[filter] = false;
      } else {
        this.errorMessage = "Accepted values are true and false";
      }
    },
    parseQuotes(input) {
      const regexp = /(\w*):"(.*?)"/gm;
      const matches = [...input.matchAll(regexp)];

      matches.forEach(match => {
        const filter = match[1];
        const value = match[2];
        if (this.validFilters.find(vfilter => vfilter.filter === filter)) {
          if (this.isBooleanFilter(filter)) {
            this.parseBooleanFilter(filter, value);
          } else {
            this.filters[filter] = value;
          }
          input = input.replace(match[0], "");
        } else {
          this.errorMessage = `Invalid filter "${filter}"`;
        }
      });

      return input;
    },
    clear() {
      this.inputValue = "";
      this.filters = {};
      this.errorMessage = undefined;
      this.$emit("search", {});
    },
    isBooleanFilter(filter) {
      const validFilter = this.validFilters.find(
        vfilter => vfilter.filter === filter
      );
      return validFilter.type === "boolean";
    },
    setFilter(item) {
      this.inputValue = this.inputValue || "";
      if (item.filter === "lastUpdated") {
        const [month, day, year] = new Date()
          .toLocaleDateString("en-US")
          .split("/");
        this.inputValue += `lastUpdated:>=${year}-${month}-${day} `;
      } else if (this.isBooleanFilter(item.filter)) {
        this.inputValue += `${item.filter}:true `;
      } else {
        this.inputValue += `${item.filter}:"search value" `;
      }
    }
  }
};
</script>
<style lang="scss" scoped>
.search {
  width: 100%;
  max-width: 420px;
  margin-top: 2px;
  font-size: 0.9rem;

  ::v-deep fieldset {
    height: 37px;
  }
  ::v-deep input {
    padding-top: 0;
  }
  ::v-deep .v-label {
    font-size: 0.9rem;
    line-height: 12px;
  }
}

.v-text-field--enclosed.v-input--dense:not(.v-text-field--solo) {
  ::v-deep .v-input__prepend-outer {
    border: solid rgba(0, 0, 0, 0.38);
    border-width: 1px 0 1px 1px;
    border-radius: 4px 0 0 4px;
    margin: 0;

    .v-btn {
      border-radius: 4px 0 0 4px;
      span {
        font-size: 0.9rem;
        text-transform: capitalize;
        letter-spacing: normal;
      }
    }

    & + .v-input__control > .v-input__slot {
      border-radius: 0 4px 4px 0;
      margin-bottom: 0;
    }
  }
  ::v-deep .v-input__append-inner,
  ::v-deep .v-input__append-outer {
    margin-top: 4px;
  }
}
</style>
