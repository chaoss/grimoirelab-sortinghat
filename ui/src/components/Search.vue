<template>
  <v-text-field
    v-model.trim="inputValue"
    append-outer-icon="mdi-magnify"
    class="search ma-0 pa-0 flex-grow-0"
    :error-messages="errorMessage"
    clearable
    label="Search"
    type="text"
    hint=" "
    persistent-hint
    @click:append-outer="search"
    @click:clear="clear"
    @keyup.enter="search"
    @focus="isFocused = true"
    @blur="isFocused = false"
  >
    <template v-slot:message="{ key, message }">
      <span>{{ message }}</span>
      <v-btn href="/search-help" target="_blank" color="primary" text x-small>
        View search syntax
        <v-icon x-small right>
          mdi-help-circle-outline
        </v-icon>
      </v-btn>
    </template>
  </v-text-field>
</template>

<script>
export default {
  name: "Search",
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
      const booleanFilters = ["isLocked", "isBot"];
      const terms = [];
      this.filters = {};
      this.errorMessage = undefined;

      if (!this.inputValue) return;

      const input = this.parseQuotes(this.inputValue);
      input.split(" ").forEach(value => {
        if (value.includes(":")) {
          const [filter, text] = value.split(":");
          if (filter === "lastUpdated") {
            this.parseLastUpdated(text);
          } else if (booleanFilters.find(bfilter => bfilter === filter)) {
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
        this.filters[match[1]] = match[2];
        input = input.replace(match[0], "");
      });

      return input;
    },
    clear() {
      this.inputValue = "";
      this.filters = {};
      this.errorMessage = undefined;
      this.$emit("search", {});
    }
  }
};
</script>
<style lang="scss" scoped>
.search {
  width: 100%;
  max-width: 500px;

  ::v-deep .v-messages__message {
    display: flex;
    justify-content: space-between;

    .v-btn__content {
      text-transform: none;
      font-weight: normal;
    }
  }
}
</style>
