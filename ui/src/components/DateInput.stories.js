import DateInput from "./DateInput.vue";

export default {
  title: "DateInput",
  excludeStories: /.*Data$/
};

const DateInputTemplate = `
  <div class="ma-5 col-3">
    <date-input v-model="date" label="Label" :filled="filled" :outlined="outlined" />
  </div>`;

export const Default = () => ({
  components: { DateInput },
  template: DateInputTemplate,
  data() {
    return {
      date: null,
      filled: false,
      outlined: false
    }
  }
});

export const Filled = () => ({
  components: { DateInput },
  template: DateInputTemplate,
  data() {
    return {
      date: null,
      filled: true,
      outlined: false
    }
  }
});

export const Outlined = () => ({
  components: { DateInput },
  template: DateInputTemplate,
  data() {
    return {
      date: null,
      filled: false,
      outlined: true
    }
  }
});

export const Error = () => ({
  components: { DateInput },
  template: DateInputTemplate,
  data() {
    return {
      date: "abc",
      filled: false,
      outlined: true
    }
  }
});
