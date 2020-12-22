<template>
  <v-hover v-slot="{ hover }">
    <v-text-field
      v-model.trim="inputValue"
      append-outer-icon="mdi-magnify"
      class="search ma-0 ml-auto pa-0 flex-grow-0"
      :class="{
        'search--hover': hover,
        'search--hidden': !inputValue && !isFocused && !errorMessage
      }"
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
  </v-hover>
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
      this.$emit("search", this.filters);
    },
    parseFilters() {
      const terms = [];
      this.filters = {};
      this.errorMessage = undefined;

      if (!this.inputValue) return;

      this.inputValue.split(" ").forEach(value => {
        if (value.includes(":")) {
          const [filter, text] = value.split(":");
          if (filter === "lastUpdated") {
            this.parseLastUpdated(text);
          } else {
            this.filters[filter] = text;
          }
        } else {
          terms.push(value);
        }
      });

      if (terms.length > 0) {
        this.filters.term = terms.join(" ");
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
    clear() {
      this.inputValue = "";
      this.filters = {};
      this.errorMessage = undefined;
      this.$emit("search", {});
    }
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

  .v-messages__message {
    display: flex;
    justify-content: space-between;

    .v-btn__content {
      text-transform: none;
      font-weight: normal;
    }
  }
}
</style>
