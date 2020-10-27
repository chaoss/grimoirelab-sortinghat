import { shallowMount, mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualsTable from "@/components/IndividualsTable";
import * as Mutations from "@/apollo/mutations";

Vue.use(Vuetify);

const deleteResponse = {
  data: {
    deleteIdentity: {
      uuid: "5f06473815dc415c9861680de8101813d9eb18e8",
      __typename: "DeleteIdentity"
    }
  }
};

const mergeResponse = {
  data: {
    merge: {
      uuid: "33697bad47122a2093d9edbbe179a72298971fd1",
      __typename: "Merge"
    }
  }
};

const unmergeResponse = {
  "data": {
    "unmergeIdentities": {
      "uuids": [
        "3db176be6859adac3a454c5377af81b1b7e3f8d8",
        "10982379421b80e13266db011d6e5131dd519016"
      ],
      "individuals": [
        {
          "profile": {
            "name": "Test 11",
            "id": "260",
            "isBot": false
          },
          "identities": [
            {
              "name": "Test 11",
              "source": "git",
              "email": "test11@example.net",
              "uuid": "3db176be6859adac3a454c5377af81b1b7e3f8d8",
              "username": "tes39"
            }
          ],
          "enrollments": []
        },
        {
          "profile": {
            "name": "Test 4",
            "id": "255",
            "isBot": false
          },
          "identities": [
            {
              "name": "Test 4",
              "source": "test",
              "email": "test4@example.net",
              "uuid": "10982379421b80e13266db011d6e5131dd519016",
              "username": "test4"
            }
          ],
          "enrollments": []
        }
      ]
    }
  }
};

describe("IndividualsTable", () => {
  test("Mock query for deleteIdentity", async () => {
    const mutate = jest.fn(() => Promise.resolve(deleteResponse));
    const wrapper = shallowMount(IndividualsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        deleteItem: mutate,
        mergeItems: () => {},
        unmergeItems: () => {},
        fetchPage: () => {}
      }
    });
    const response = await Mutations.deleteIdentity(wrapper.vm.$apollo, "5f06473815dc415c9861680de8101813d9eb18e8");

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for merge", async () => {
    const mutate = jest.fn(() => Promise.resolve(mergeResponse));
    const wrapper = shallowMount(IndividualsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        mergeItems: mutate,
        unmergeItems: () => {},
        deleteItem: () => {},
        fetchPage: () => {}
      }
    });
    const response = await Mutations.deleteIdentity(wrapper.vm.$apollo, "5f06473815dc415c9861680de8101813d9eb18e8");

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for unmerge", async () => {
    const mutate = jest.fn(() => Promise.resolve(unmergeResponse));
    const wrapper = shallowMount(IndividualsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        unmergeItems: mutate,
        mergeItems: () => {},
        deleteItem: () => {},
        fetchPage: () => {}
      }
    });
    const response = await Mutations.unmerge(wrapper.vm.$apollo, [
      "3db176be6859adac3a454c5377af81b1b7e3f8d8",
      "10982379421b80e13266db011d6e5131dd519016"
    ]);

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});
