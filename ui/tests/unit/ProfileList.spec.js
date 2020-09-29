import { shallowMount, mount, createLocalVue } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import ProfileList from "@/components/ProfileList";
import * as Queries from "@/apollo/queries";

Vue.use(Vuetify);

const profileMocked = {
  data: {
    individuals: {
      entities: [{
        isLocked: false,
        profile: {
          name: "Test Name"
        },
        identities: [{
          name: "Test Name",
          source: "github",
          email: "test@example.net",
          uuid: "7a727227226daae693c61ddf7040e51c97ac638d",
          username: "test"
        }],
        enrollments: []
      }],
      __typename: "IdentityPaginatedType"
    }
  }
};

describe("ProfileList", () => {
  test("Mock query for getProfileByUuid", async () => {
    const query = jest.fn(() => Promise.resolve(profileMocked));
    const wrapper = shallowMount(ProfileList, {
      Vue,
      mocks: {
        $apollo: {
          query
        }
      },
      computed: {
        selectedIndividual: () => {
          return {
            uuid: "12abc",
            selected: true
          }
        }
      }
    });
    const response = await Queries.getProfileByUuid(wrapper.vm.$apollo, wrapper.vm.selectedIndividual.uuid);
    expect(query).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Queries profile data when selected", async () => {
    const getProfileByUuidSpied = spyOn(Queries, "getProfileByUuid");
    const query = jest.fn(() => Promise.resolve(profileMocked));
    const wrapper = shallowMount(ProfileList, {
      Vue,
      attachToDocument: true,
      mocks: {
        $apollo: {
          query
        }
      },
      computed: {
        selectedIndividual: () => {}
      }
    });

    wrapper.vm.$options.watch.selectedIndividual.call(wrapper.vm, {
      uuid: "12abc",
      selected: true
    });

    expect(getProfileByUuidSpied).toHaveBeenCalledWith(wrapper.vm.$apollo, "12abc");
  });

  test("Shows selected profile", async () => {
    const localVue = createLocalVue();
    const vuetify = new Vuetify();
    const query = jest.fn(() => Promise.resolve(profileMocked));
    const wrapper = mount(ProfileList, {
      Vue,
      vuetify,
      mocks: {
        $apollo: {
          query
        }
      },
      data() {
        return {
          profiles: []
        }
      },
      computed: {
        selectedIndividual: () => {}
      }
    });

    wrapper.vm.$options.watch.selectedIndividual.call(wrapper.vm, {
      uuid: "12abc",
      selected: true
    });

    await Vue.nextTick();
    expect(wrapper.vm.profiles.length).toBe(1);
    await Vue.nextTick();
    expect(wrapper.find('.v-navigation-drawer--open').exists()).toBe(true);
    expect(wrapper.findAll('.v-list-item__title').at(1).text()).toBe("Test Name");
    expect(wrapper.element).toMatchSnapshot();
  });
});
