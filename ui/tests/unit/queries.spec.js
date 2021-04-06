import { shallowMount, mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualsData from "@/components/IndividualsData";
import IndividualsTable from "@/components/IndividualsTable";
import OrganizationsTable from "@/components/OrganizationsTable";
import JobsTable from "@/components/JobsTable";
import * as Queries from "@/apollo/queries";

Vue.use(Vuetify);

const responseMocked = {
  data: {
    individuals: {
      entities: [
        {
          mk: "172188fd88c1df2dd6d187b6f32cb6aced544aee",
          identities: [{ name: "test name", __typename: "IdentityType" }],
          profile: {
            id: "7",
            name: "test name",
            __typename: "ProfileType"
          },
          __typename: "IndividualType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        hasNext: false,
        hasPrev: false,
        startIndex: 1,
        endIndex: 1,
        totalResults: 1
      },
      __typename: "IdentityPaginatedType"
    }
  }
};

const paginatedResponse = {
  data: {
    individuals: {
      entities: [
        {
          isLocked: false,
          profile: {
            name: "Test",
            id: "15",
            email: "test6@example.net",
            __typename: "ProfileType"
          },
          identities: [
            {
              name: "Test",
              source: "test",
              email: "test6@example.net",
              uuid: "03b3428eea9c7f29b4f8238b58dc6ecd84bf176a",
              username: "test6",
              __typename: "IdentityType"
            }
          ],
          enrollments: [],
          __typename: "IndividualType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 1,
        numPages: 2,
        totalResults: 2,
        __typename: "PaginationType"
      },
      __typename: "IdentityPaginatedType"
    }
  }
};

const paginatedOrganizations = {
  data: {
    organizations: {
      entities: [
        {
          name: "Test 1",
          enrollments: [
            { id: 1, __typename: "EnrollmentType" },
            { id: 2, __typename: "EnrollmentType" }
          ],
          __typename: "OrganizationType"
        },
        {
          name: "Test 2",
          enrollments: [
            { id: 3, __typename: "EnrollmentType" },
            { id: 4, __typename: "EnrollmentType" }
          ],
          __typename: "OrganizationType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        totalResults: 2,
        __typename: "PaginationType"
      },
      __typename: "OrganizationPaginatedType"
    }
  }
};

const countriesMocked = {
  data: {
    countries: {
      entities: [
        { code: "AD", name: "Andorra" },
        { code: "AE", name: "United Arab Emirates" },
        { code: "AF", name: "Afghanistan" },
        { code: "AG", name: "Antigua and Barbuda" },
        { code: "AI", name: "Anguilla" },
        { code: "AL", name: "Albania" },
        { code: "AM", name: "Armenia" }
      ],
      __typename: "CountryPaginatedType"
    }
  }
};

const jobsMocked = {
  data: {
    jobs: {
      entities: [
        {
          jobId: "41f813e5-6701-41d2-bfac-ac13e04d4858",
          status: "queued",
          jobType: "unify",
          errors: [],
          result: []
        }
      ],
      pageInfo: {
        page: 2,
        numPages: 2,
        totalResults: 11,
        hasNext: false,
        hasPrev: true
      }
    }
  }
};

describe("IndividualsData", () => {
  test("mock query for getIndividuals", async () => {
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = shallowMount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      },
      data() {
        return {
          individuals_mocked: null
        };
      }
    });
    let response = await Queries.getIndividuals.query(wrapper.vm.$apollo);
    let individuals_mocked = response.data;
    await wrapper.setData({
      individuals_mocked
    });
    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("getIndividuals with arguments", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");

    let response = await Queries.getIndividuals.query(undefined, 10, 100);
    expect(getIndividualsSpied).toHaveBeenLastCalledWith(undefined, 10, 100);
  });

  test("getIndividuals with default arguments in the IndividualsData component", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = mount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      }
    });

    expect(getIndividualsSpied).toBeCalled();
    expect(getIndividualsSpied).toHaveBeenCalledWith(wrapper.vm.$apollo, 50);
  });

  test("infinite scroll won't call for more individuals if the page is not at the bottom", async () => {
    const getIndividualsSpied = spyOn(Queries.getIndividuals, "query");
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = mount(IndividualsData, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getindividuals: {
          query: Queries.getIndividuals.query
        }
      }
    });
    wrapper.vm.scroll();

    expect(getIndividualsSpied).toBeCalled();
    expect(getIndividualsSpied).toHaveBeenCalledTimes(1);
  });
});

describe("IndividualsTable", () => {
  const mountFunction = options => {
    return shallowMount(IndividualsTable, {
      Vue,
      propsData: {
        fetchPage: () => {},
        mergeItems: () => {},
        unmergeItems: () => {},
        moveItem: () => {},
        deleteItem: () => {},
        addIdentity: () => {},
        updateProfile: () => {},
        enroll: () => {},
        getCountries: () => {},
        lockIndividual: () => {},
        unlockIndividual: () => {},
        withdraw: () => {},
        updateEnrollment: () => {}
      },
      ...options
    });
  };

  test("Mock query for getPaginatedIndividuals", async () => {
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: query });
    const response = await Queries.getPaginatedIndividuals(
      wrapper.vm.$apollo,
      1,
      1
    );

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Searches by term", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { term: "test" } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, { term: "test" }, null);
  });

  test("Searches by gender", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { gender: "gender" } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(
      1,
      10,
      { gender: "gender" },
      null
    );
  });

  test("Searches by lastUpdated", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({
      filters: { lastUpdated: "<2000-01-01T00:00:00.000Z" }
    });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(
      1,
      10,
      {
        lastUpdated: "<2000-01-01T00:00:00.000Z"
      },
      null
    );
  });

  test("Searches by isBot", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { isBot: true } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, { isBot: true }, null);
  });

  test("Searches by country", async () => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ filters: { country: "Spain" } });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, { country: "Spain" }, null);
  });

  test.each([
    "lastModified",
    "createdAt"
  ])("Orders query by %p", async (value) => {
    const querySpy = spyOn(Queries, "getPaginatedIndividuals");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ fetchPage: Queries.getPaginatedIndividuals });
    await wrapper.setData({ orderBy: value });

    const response = await wrapper.vm.queryIndividuals(1);

    expect(querySpy).toHaveBeenCalledWith(1, 10, {}, value);
  });

  test("Mock query for getCountries", async () => {
    const query = jest.fn(() => Promise.resolve(countriesMocked));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          query
        }
      }
    });
    await wrapper.setProps({ getCountries: query });
    const response = await Queries.getCountries(wrapper.vm.$apollo);

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("OrganizationsTable", () => {
  test("Mock query for getPaginatedOrganizations", async () => {
    const query = jest.fn(() => Promise.resolve(paginatedOrganizations));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        fetchPage: query,
        enroll: () => {},
        addDomain: () => {},
        addOrganization: () => {},
        deleteDomain: () => {},
        deleteOrganization: () => {}
      }
    });
    const response = await Queries.getPaginatedOrganizations(
      wrapper.vm.$apollo,
      1,
      1
    );

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock search by term", async () => {
    const querySpy = spyOn(Queries, "getPaginatedOrganizations");
    const query = jest.fn(() => Promise.resolve(paginatedResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        fetchPage: Queries.getPaginatedOrganizations,
        enroll: () => {},
        addDomain: () => {},
        addOrganization: () => {},
        deleteDomain: () => {},
        deleteOrganization: () => {}
      },
      data() {
        return {
          filters: { term: "Bitergia" }
        };
      }
    });

    const response = await wrapper.vm.getOrganizations();

    expect(querySpy).toHaveBeenCalledWith(1, 10, { term: "Bitergia" });
  });
});

describe("JobsTable", () => {
  test("Mock query for getJobs", async () => {
    const query = jest.fn(() => Promise.resolve(jobsMocked));
    const wrapper = shallowMount(JobsTable, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      propsData: {
        getJobs: query
      }
    });
    const response = await Queries.getJobs(wrapper.vm.$apollo, 2, 10);

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
    expect(wrapper.vm.jobs.length).toBe(1);
    expect(wrapper.vm.page).toBe(2);
    expect(wrapper.vm.pageCount).toBe(2);
  });
});
