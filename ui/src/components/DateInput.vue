<template>
  <v-menu
    v-model="openPicker"
    :close-on-content-click="false"
    transition="scale-transition"
    min-width="290px"
    nudge-bottom="60"
    right
  >
    <template v-slot:activator="{ on }">
      <v-text-field
        v-model="inputDate"
        :label="label"
        :filled="filled"
        :dense="outlined"
        :outlined="outlined"
        :single-line="singleLine"
        :error-messages="error"
        :rules="isValid"
        height="30"
        clearable
        hide-details="auto"
        hint="YYYY-MM-DD"
        v-on="on"
        @change="formatDate($event)"
        @click:clear="formatDate()"
      ></v-text-field>
    </template>
    <v-date-picker
      v-model="pickerDate"
      :min="min"
      :max="max"
      no-title
      scrollable
      @input="formatDate($event)"
    />
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
    },
    singleLine: {
      type: Boolean,
      required: false,
      default: false
    }
  },
  data() {
    return {
      openPicker: false,
      error: null,
      inputDate: this.value,
      pickerDate: this.value,
      isValid: [value => (value ? !this.error : true)]
    };
  },
  methods: {
    setError(error) {
      this.error = error;
    },
    formatDate(date) {
      this.setError(null);
      this.openPicker = false;
      if (date) {
        try {
          const ISODate = new Date(date).toISOString();
          const dateString = ISODate.substring(0, 10);
          this.$emit("input", ISODate);
          this.inputDate = dateString;
          this.pickerDate = dateString;
        } catch {
          this.setError("Invalid date");
          this.pickerDate = "";
        }
      } else {
        this.$emit("input", null);
        this.inputDate = "";
        this.pickerDate = "";
      }
    }
  },
  watch: {
    value(newValue) {
      this.formatDate(newValue);
    }
  },
  mounted() {
    this.formatDate(this.value);
  }
};
</script>
