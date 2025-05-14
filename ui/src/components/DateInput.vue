<template>
  <div>
    <v-text-field
      v-model="inputDate"
      :density="variant == 'outlined' ? 'comfortable' : 'default'"
      :error-messages="error"
      :label="label"
      :variant="variant"
      :single-line="singleLine"
      :rules="isValid"
      height="30"
      clearable
      hint="YYYY-MM-DD"
      @change="formatDate(inputDate)"
      @click:clear="formatDate()"
      @update:focused="() => {}"
    >
    </v-text-field>
    <v-menu
      v-model="openPicker"
      :close-on-content-click="false"
      activator="parent"
      location="right"
      transition="scale-transition"
      min-width="290px"
      offset-x
    >
      <v-date-picker
        v-model="pickerDate"
        :min="min"
        :max="max"
        color="primary"
        hide-header
        hide-weekdays
        @update:model-value="formatDate($event)"
      />
    </v-menu>
  </div>
</template>

<script>
import { useDate } from "vuetify";

export default {
  name: "DateInput",
  props: {
    modelValue: {
      type: [String, Date],
    },
    label: {
      type: String,
      required: true,
    },
    min: {
      type: [String, Date],
      required: false,
    },
    max: {
      type: [String, Date],
      required: false,
    },
    variant: {
      type: String,
      required: false,
      default: "outlined",
    },
    singleLine: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      dateFormatter: null,
      openPicker: false,
      error: null,
      inputDate: this.modelValue,
      pickerDate: null,
      isValid: [(value) => (value ? !this.error : true)],
    };
  },
  emits: ["update:modelValue"],
  methods: {
    setError(error) {
      this.error = error;
    },
    formatDate(date) {
      this.setError(null);
      this.openPicker = false;
      if (date) {
        try {
          const dateObject = this.dateFormatter.date(date);
          const dateString = this.dateFormatter.toISO(dateObject);
          const dateTime = `${dateString}T00:00:00+00:00`;

          this.inputDate = dateString;
          this.pickerDate = dateString;
          this.$emit("update:modelValue", dateTime);
        } catch {
          this.setError("Invalid date");
          this.pickerDate = null;
        }
      } else {
        this.$emit("update:modelValue", null);
        this.inputDate = "";
        this.pickerDate = null;
      }
    },
  },
  mounted() {
    this.dateFormatter = useDate();
    this.formatDate(this.modelValue);
  },
};
</script>
<style lang="scss" scoped>
:deep(.v-field.v-field--appended) {
  --v-field-padding-end: 0;
}
:deep(.v-field__clearable) {
  margin-inline: 2px;
}
</style>
