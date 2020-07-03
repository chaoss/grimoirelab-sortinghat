import { shallowMount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import App from "@/App";
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
      __typename: "IdentityPaginatedType"
    },
    pageInfo: {
      page: 1,
      pageSize: 10,
      numPages: 1,
      hasNext: false,
      hasPrev: false,
      startIndex: 1,
      endIndex: 1,
      totalResults: 1
    }
  }
};

describe("App", () => {
  test("mock query for getIndividuals", async () => {
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = shallowMount(App, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      }
    });
    let response = await Queries.getIndividuals(wrapper.vm.$apollo);
    let individuals_mocked = response.data;
    await wrapper.setData({
      individuals_mocked
    });

    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
    expect(wrapper.vm.individuals).toBe(responseMocked.data.individuals);
  });

  test("getIndividuals with arguments", async () => {
    const getIndividualsSpied = spyOn(Queries, "getIndividuals");
    
    let response = await Queries.getIndividuals(undefined, 10, 100);
    expect(getIndividualsSpied).toHaveBeenLastCalledWith(undefined, 10, 100);
  });

  test("getIndividuals without arguments in the App component", async () => {
    const getIndividualsSpied = spyOn(Queries, "getIndividuals");
    const query = jest.fn(() => Promise.resolve(responseMocked));
    const wrapper = shallowMount(App, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      }
    });

    expect(getIndividualsSpied).toBeCalled();
    expect(getIndividualsSpied).toHaveBeenCalledWith(wrapper.vm.$apollo);
  });
});
