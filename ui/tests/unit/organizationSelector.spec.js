import { mount } from "@vue/test-utils";
import vuetify from "@/plugins/vuetify";
import OrganizationSelector from "@/components/OrganizationSelector";

const termResults = {
  entities: [
    { name: "Boeing", aliases: [] },
    { name: "Booking", aliases: [] },
    { name: "Consulting", aliases: [] },
  ],
};

describe("OrganizationSelector", () => {
  const mountFunction = (fetchOrganizations) => {
    return mount(OrganizationSelector, {
      global: {
        plugins: [vuetify],
      },
      props: {
        fetchOrganizations,
        addOrganization: jest.fn(),
      },
    });
  };

  test("Adds an exact match missing from the search results", async () => {
    const fetchOrganizations = jest.fn((page, items, filters) => {
      if (filters.name) {
        return { entities: [{ name: "ING", aliases: [] }] };
      }
      return termResults;
    });
    const wrapper = mountFunction(fetchOrganizations);

    await wrapper.vm.getSelectorItems("ing");

    expect(fetchOrganizations).toHaveBeenCalledWith(1, 10, { term: "ing" });
    expect(fetchOrganizations).toHaveBeenCalledWith(1, 10, { name: "ing" });
    expect(wrapper.vm.organizations.map((org) => org.name)).toEqual([
      "ING",
      "Boeing",
      "Booking",
      "Consulting",
    ]);

    wrapper.vm.searchValue = "ing";
    expect(wrapper.vm.appendContent).toBe(false);
  });

  test("Does not search again when the results include the term", async () => {
    const fetchOrganizations = jest.fn(() => ({
      entities: [
        { name: "Example Inc.", aliases: [{ alias: "Example" }] },
        { name: "Examples", aliases: [] },
      ],
    }));
    const wrapper = mountFunction(fetchOrganizations);
    fetchOrganizations.mockClear();

    await wrapper.vm.getSelectorItems("example");

    expect(fetchOrganizations).toHaveBeenCalledTimes(1);
    expect(wrapper.vm.organizations).toHaveLength(2);
  });

  test("Offers to create the organization when there is no exact match", async () => {
    const fetchOrganizations = jest.fn((page, items, filters) => {
      if (filters.name) {
        return { entities: [] };
      }
      return termResults;
    });
    const wrapper = mountFunction(fetchOrganizations);

    await wrapper.vm.getSelectorItems("ing");

    expect(wrapper.vm.organizations).toHaveLength(3);
    wrapper.vm.searchValue = "ing";
    expect(wrapper.vm.appendContent).toBe(true);
  });
});
