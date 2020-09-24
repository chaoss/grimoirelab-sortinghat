import { shallowMount, mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualsData from "@/components/IndividualsData";
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
        }
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
