import { mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import Search from "@/components/Search";

Vue.use(Vuetify);

describe("Search", () => {
  const vuetify = new Vuetify();
  const mountFunction = options => {
    return mount(Search, {
      Vue,
      vuetify,
      ...options,
    })
  };

  test.each([
    ["test", "test"],
    ["two words", "two words"],
    ["test lastUpdated:>2020", "test"],
    ["lastUpdated:2019..2020 test", "test"]
  ])("Given %p parses term", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value })
    });

    const button = wrapper.find("button.mdi-magnify");
    await button.trigger("click");

    expect(wrapper.vm.filters.term).toBe(expected);
  });

  test.each([
    ["lastUpdated:<2000", "<2000-01-01T00:00:00.000Z"],
    ["lastUpdated:<=2000-08-10", "<=2000-08-10T00:00:00.000Z"],
    ["lastUpdated:>2000", ">2000-01-01T00:00:00.000Z"],
    ["lastUpdated:>=2000-02-03", ">=2000-02-03T00:00:00.000Z"],
    [
      "lastUpdated:2000..2001",
      "2000-01-01T00:00:00.000Z..2001-01-01T00:00:00.000Z"
    ],
    ["test lastUpdated:<2000", "<2000-01-01T00:00:00.000Z"]
  ])("Given %p parses lastUpdated filter", async (value, expected) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value })
    });

    const button = wrapper.find("button.mdi-magnify");
    await button.trigger("click");

    expect(wrapper.vm.filters.lastUpdated).toBe(expected);
  });

  test.each([
    "lastUpdated:abc",
    "lastUpdated:<abc",
    "lastUpdated:<2000-23-01",
    "lastUpdated:>=2000-01-49",
    "lastUpdated:>@",
    "lastUpdated:2000-2001",
    "lastUpdated:===2000-01-01",
    "lastUpdated:<=2000-01-01>=2000-01-01"
  ])("Given an invalid value %p renders an error", async (value) => {
    const wrapper = mountFunction({
      data: () => ({ inputValue: value })
    });

    const button = wrapper.find("button.mdi-magnify");
    await button.trigger("click");
    const errorMessage = wrapper.find(".v-messages__message");

    expect(errorMessage.exists()).toBe(true);
  });
});
