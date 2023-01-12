import { mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import DateInput from "@/components/DateInput";

Vue.use(Vuetify);

describe("DateInput", () => {
  const vuetify = new Vuetify();
  const mountFunction = (options) => {
    return mount(DateInput, {
      Vue,
      vuetify,
      ...options,
      props: {
        label: "Label",
      },
    });
  };

  test("Sets date in the right formats", async () => {
    const wrapper = mountFunction();
    await wrapper.setProps({ value: "2020" });

    // YYYYYY-MM-DD format in the UI
    expect(wrapper.vm.inputDate).toBe("2020-01-01");
    expect(wrapper.vm.pickerDate).toBe("2020-01-01");

    // Emit ISO date for the v-model
    expect(wrapper.emitted().input[1]).toEqual(["2020-01-01T00:00:00.000Z"]);
  });

  test("Shows an error for an invalid date", async () => {
    const wrapper = mountFunction();
    await wrapper.setProps({ value: "invalid date" });

    expect(wrapper.vm.error).toBe("Invalid date");
    expect(wrapper.find(".error--text").exists()).toBe(true);
  });
});
