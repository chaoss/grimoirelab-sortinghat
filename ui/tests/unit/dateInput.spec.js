import { mount } from "@vue/test-utils";
import vuetify from "@/plugins/vuetify";
import DateInput from "@/components/DateInput";

describe("DateInput", () => {
  const mountFunction = (options) => {
    return mount(DateInput, {
      global: {
        plugins: [vuetify],
      },
      ...options,
    });
  };

  test("Sets date in the right formats", async () => {
    const wrapper = mountFunction({ props: { modelValue: "2020", label: "Label" } });
    wrapper.find("input").trigger("change");

    // YYYYYY-MM-DD format in the UI
    expect(wrapper.vm.inputDate).toBe("2020-01-01");
    expect(wrapper.vm.pickerDate.toJSON()).toMatch("2020-01-01");

    // Emit ISO date for the v-model
    expect(wrapper.emitted("update:modelValue")[1]).toEqual([
      "2020-01-01T00:00:00+00:00",
    ]);
  });

  test("Shows an error for an invalid date", async () => {
    const wrapper = mountFunction({ props: { modelValue: "invalid date",label: "Label" } });

    expect(wrapper.vm.error).toBe("Invalid date");
    expect(wrapper.find('[role="alert"]').exists()).toBe(true);
  });
});
