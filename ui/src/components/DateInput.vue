<template>
  <v-menu
    v-model="openPicker"
    :close-on-content-click="false"
    transition="scale-transition"
    min-width="290px"
    nudge-bottom="40"
    right
  >
    <template v-slot:activator="{ on }">
      <v-text-field
        v-model="inputDate"
        :label="label"
        :filled="filled"
        :dense="outlined"
        :outlined="outlined"
        :single-line="outlined"
        :error-messages="error"
        height="30"
        clearable
        hide-details="auto"
        v-on="on"
        @change="setInputDate($event)"
      ></v-text-field>
    </template>
    <v-date-picker v-model="date" :min="min" :max="max" no-title scrollable>
    </v-date-picker>
  </v-menu>
</template>

<script>
export default {
  name: "DateInput",
  props: {
    value: {
      type: [String, Date]
    },
    label: {
      type: String,
      required: true
    },
    min: {
      type: [String, Date],
      required: false
    },
    max: {
      type: [String, Date],
      required: false
    },
    filled: {
      type: Boolean,
      required: false,
      default: false
    },
    outlined: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data() {
    return {
      openPicker: false,
      error: null,
      inputDate: this.value
    };
  },
  computed: {
    date: {
      get() {
        try {
          const ISODate = this.value
            ? new Date(this.value).toISOString()
            : null;
          this.setInputDate(ISODate);
          return ISODate;
        } catch {
          this.setError("Invalid date");
          return null;
        }
      },
      set(value) {
        const ISODate = new Date(value).toISOString();
        this.$emit("input", ISODate);
        this.openPicker = false;
        this.setInputDate(ISODate);
        this.setError(null);
      }
    }
  },
  methods: {
    setError(error) {
      this.error = error;
    },
    setInputDate(date) {
      if (!date) {
        return;
      }
      try {
        const ISODate = date ? new Date(date).toISOString() : null;
        this.$emit("input", ISODate);
        this.setError(null);
        this.openPicker = false;
        this.inputDate = ISODate.substring(0, 10);
      } catch {
        this.setError("Invalid date");
      }
    }
  }
};
</script>
