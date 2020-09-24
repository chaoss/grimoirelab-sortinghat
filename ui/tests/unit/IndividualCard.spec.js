import { shallowMount, mount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualCard from "@/components/IndividualCard";
import * as Mutations from "@/apollo/mutations";

Vue.use(Vuetify);

const lockResponseMocked = {
  data: {
    lock: {
      uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
      individual: {
        isLocked: true,
        __typename: "IndividualType"
      },
      __typename: "Lock"
    }
  }
};

const unlockResponseMocked = {
  data: {
    unlock: {
      uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
      individual: {
        isLocked: false,
        __typename: "IndividualType"
      },
      __typename: "Unlock"
    }
  }
};

const errorResponseMocked = {
  errors: [
    {
      message: "abc not found in the registry",
      locations:[{line:2,column:3}],
      path:["lock"],
      extensions:{
        code:9
      }
    }],
    data:{
      lock:null
    }};

describe("IndividualCard", () => {
  test("Mock query for lockIndividual", async () => {
    const mutate = jest.fn(() => Promise.resolve(lockResponseMocked));
    const wrapper = shallowMount(IndividualCard, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        name: 'Test',
        uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
        isLocked: false
      }
    });

    const response = await Mutations.lockIndividual(wrapper.vm.$apollo, wrapper.vm.uuid);

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
    });

    test("Mock query for unlockIndividual", async () => {
      const mutate = jest.fn(() => Promise.resolve(unlockResponseMocked));
      const wrapper = shallowMount(IndividualCard, {
        Vue,
        mocks: {
          $apollo: {
            mutate
          }
        },
        propsData: {
          name: 'Test',
          uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
          isLocked: true
        }
      });

      const response = await Mutations.unlockIndividual(wrapper.vm.$apollo, wrapper.vm.uuid);

      expect(mutate).toBeCalled();
      expect(wrapper.element).toMatchSnapshot();
      });

      test("Lock individual on click", async () => {
        const mutate = jest.fn(() => Promise.resolve(lockResponseMocked));
        const lockIndividual = jest.spyOn(Mutations, 'lockIndividual');
        const wrapper = mount(IndividualCard, {
          Vue,
          mocks: {
            $apollo: {
              mutate
            }
          },
          propsData: {
            name: 'Test',
            uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
            isLocked: false
          }
        });

        wrapper.find('button').trigger('click');

        expect(mutate).toBeCalled();
        expect(lockIndividual).toHaveBeenCalledWith(wrapper.vm.$apollo, "375458370ac0323bfb2e5a153e086551ef628d53");
        await Vue.nextTick();
        expect(wrapper.vm.locked).toBe(true);
        await Vue.nextTick();
        expect(wrapper.find('.mdi-lock').exists()).toBe(true);
        expect(wrapper.element).toMatchSnapshot();
      });

      test("Unlock individual on click", async () => {
        const mutate = jest.fn(() => Promise.resolve(unlockResponseMocked));
        const unlockIndividual = jest.spyOn(Mutations, 'unlockIndividual');
        const wrapper = mount(IndividualCard, {
          Vue,
          mocks: {
            $apollo: {
              mutate
            }
          },
          propsData: {
            name: 'Test',
            uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
            isLocked: true
          }
        });

        wrapper.find('button').trigger('click');

        expect(mutate).toBeCalled();
        expect(unlockIndividual).toHaveBeenCalledWith(wrapper.vm.$apollo, "375458370ac0323bfb2e5a153e086551ef628d53");
        await Vue.nextTick();
        expect(wrapper.vm.locked).toBe(false);
        await Vue.nextTick();
        expect(wrapper.find('.mdi-lock-open-outline').exists()).toBe(true);
        expect(wrapper.element).toMatchSnapshot();
      });

      test("Show snackbar on error", async () => {
        const mutate = jest.fn(() => Promise.resolve(errorResponseMocked));
        const wrapper = mount(IndividualCard, {
          Vue,
          mocks: {
            $apollo: {
              mutate
            }
          },
          propsData: {
            name: 'Test',
            uuid: "abc",
            isLocked: true
          }
        });

        wrapper.find('button').trigger('click');

        expect(mutate).toBeCalled();
        await Vue.nextTick();
        expect(wrapper.vm.snackbar.text).toBe("abc not found in the registry");
        await Vue.nextTick();
        expect(wrapper.find('.v-snack').exists()).toBe(true);
        expect(wrapper.element).toMatchSnapshot();
      });
  });
