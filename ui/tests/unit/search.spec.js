import { mount } from "@vue/test-utils";
import vuetify from "@/plugins/vuetify";
import Search from "@/components/Search";

describe("Search", () => {
  const mountFunction = (options) => {
    return mount(Search, {
      global: {
        plugins: [vuetify],
      },
      ...options,
    });
  };

  test.each([
    ["test", "test"],
    ["two words", "two words"],
    ["test lastUpdated:>2020", "test"],
    ["lastUpdated:2019..2020 test", "test"],
  ])("Given %p parses term", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.term).toBe(expected);
  });

  test.each([
    ["dateFilter:<2000", "<2000-01-01T00:00:00.000Z"],
    ['dateFilter:"<2000"', "<2000-01-01T00:00:00.000Z"],
    ["dateFilter:<=2000-08-10", "<=2000-08-10T00:00:00.000Z"],
    ["dateFilter:>2000", ">2000-01-01T00:00:00.000Z"],
    ["dateFilter:>=2000-02-03", ">=2000-02-03T00:00:00.000Z"],
    [
      "dateFilter:2000..2001",
      "2000-01-01T00:00:00.000Z..2001-01-01T00:00:00.000Z",
    ],
    ["test dateFilter:<2000", "<2000-01-01T00:00:00.000Z"],
  ])("Given %p parses date filter", async (value, expected) => {
    const wrapper = mountFunction({
      propsData: {
        validFilters: [
          {
            filter: "dateFilter",
            type: "date",
          },
        ],
      },
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.dateFilter).toBe(expected);
  });

  test.each([
    "lastUpdated:abc",
    "lastUpdated:<abc",
    "lastUpdated:<2000-23-01",
    "lastUpdated:>=2000-01-49",
    "lastUpdated:>@",
    "lastUpdated:2000-2001",
    "lastUpdated:===2000-01-01",
    "lastUpdated:<=2000-01-01>=2000-01-01",
    "isBot:1",
    "isBot:falsee",
  ])("Given an invalid value %p renders an error", async (value) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");
    const errorMessage = wrapper.find('[role="alert"]');

    expect(errorMessage.exists()).toBe(true);
  });

  test.each([
    ["gender:test", "test"],
    [`gender:"two words"`, "two words"],
  ])("Given %p parses gender", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.gender).toBe(expected);
  });

  test.each([
    [`country:"United Kingdom"`, "United Kingdom"],
    [`country:"United States of America"`, "United States of America"],
    ["country:Spain", "Spain"],
    [`country:"UK"`, "UK"],
  ])("Given %p parses country filter", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.country).toBe(expected);
  });

  test.each([
    ["source:git", "git"],
    [`source:"git"`, "git"],
    [`source:"docker hub"`, "docker hub"],
    [`test source:"docker hub"`, "docker hub"],
  ])("Given %p parses source", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value }),
    });

    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.source).toBe(expected);
  });

  test.each(["invalidFilter:value", `invalidFilter:"value"`])(
    "Given an invalid filter %p shows an error",
    async (value) => {
      const wrapper = mountFunction({
        props: {
          validFilters: [
            {
              filter: "validFilter",
              type: "string",
            },
          ],
        },
        data: () => ({ inputValue: value }),
      });

      const button = wrapper.find('[role="button"].mdi-magnify');
      await button.trigger("click");
      const errorMessage = wrapper.find('[role="alert"]');

      expect(errorMessage.exists()).toBe(true);
    }
  );

  test.each([
    ["booleanFilter:true", true],
    ["booleanFilter:false", false],
    [`booleanFilter:"true"`, true],
    [`booleanFilter:"false"`, false],
  ])("Parses a boolean filter %p", async (value, expected) => {
    const wrapper = mountFunction({
      propsData: {
        validFilters: [
          {
            filter: "booleanFilter",
            type: "boolean",
          },
        ],
      },
      data: () => ({ inputValue: value }),
    });
    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");

    expect(wrapper.vm.filters.booleanFilter).toBe(expected);
  });

  test.each([
    "booleanFilter:truee",
    "booleanFilter:falsee",
    "booleanFilter:123",
    `booleanFilter:"trueeee"`,
  ])("Shows an error for an invalid boolean filter value %p", async (value) => {
    const wrapper = mountFunction({
      propsData: {
        validFilters: [
          {
            filter: "booleanFilter",
            type: "boolean",
          },
        ],
      },
      data: () => ({ inputValue: value }),
    });
    const button = wrapper.find('[role="button"].mdi-magnify');
    await button.trigger("click");
    const errorMessage = wrapper.find('[role="alert"]');

    expect(errorMessage.exists()).toBe(true);
  });

  test.each([
    [{ filter: "booleanFilter", type: "boolean" }, "booleanFilter:true"],
    [{ filter: "stringFilter", type: "string" }, `stringFilter:"search value"`],
  ])(
    "Shows selected filter on the search box",
    async (validFilters, expected) => {
      const wrapper = mountFunction({
        propsData: {
          filterSelector: true,
          validFilters: [validFilters],
        },
      });
      // Set an element data-app to avoid Vuetify warnings
      // https://github.com/vuetifyjs/vuetify/issues/3456
      const el = document.createElement("div");
      el.setAttribute("data-v-app", true);
      document.body.appendChild(el);

      const button = wrapper.find(".v-input__prepend .v-btn");
      await button.trigger("click");
      const filter = wrapper.find(".v-list-item");
      await filter.trigger("click");

      expect(wrapper.vm.inputValue).toContain(expected);
    }
  );

  test("Adds spaces when multiple filters are set", async () => {
    const wrapper = mountFunction({
      propsData: {
        filterSelector: true,
        validFilters: [
          { filter: "booleanFilter", type: "boolean" },
          { filter: "stringFilter", type: "string" },
        ],
      },
      data: () => ({ inputValue: "text" }),
    });
    const el = document.createElement("div");
    el.setAttribute("data-app", true);
    document.body.appendChild(el);

    // Add filters when there is text on the search box
    const button = wrapper.find(".v-input__prepend .v-btn");
    await button.trigger("click");
    const filter1 = wrapper.findAll(".v-list-item").at(0);
    const filter2 = wrapper.findAll(".v-list-item").at(1);
    await filter1.trigger("click");
    await filter2.trigger("click");

    expect(wrapper.vm.inputValue).toBe(
      'text booleanFilter:true stringFilter:"search value" '
    );

    // Clear the search box and add filters
    await wrapper.find('[aria-label="Clear Search"]').trigger("click");
    await button.trigger("click");
    await filter1.trigger("click");
    await filter2.trigger("click");

    expect(wrapper.vm.inputValue).toBe(
      'booleanFilter:true stringFilter:"search value" '
    );
  });

  test("Emits the selected order", async () => {
    const orderOption = { text: "Order text", value: "ordervalue" };
    const wrapper = mountFunction({
      propsData: {
        orderSelector: true,
        orderOptions: [orderOption],
      },
    });
    const select = wrapper.findComponent({ ref: "orderSelector" });
    select.setValue("ordervalue");

    // Default descending order
    expect(wrapper.vm.order.value).toBe("ordervalue");
    expect(wrapper.vm.order.descending).toBe(true);
    expect(wrapper.emitted().search[0][1]).toBe("-ordervalue");

    // Ascending order
    const button = wrapper.find(".select .v-input__prepend .v-btn");
    await button.trigger("click");

    expect(wrapper.vm.order.descending).toBe(false);
    expect(wrapper.emitted().search[1][1]).toBe("ordervalue");
  });
});
