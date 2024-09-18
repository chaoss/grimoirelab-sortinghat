import { h, nextTick } from "vue";
import { mount } from "@vue/test-utils";
import { VApp } from "vuetify/components";
import vuetify from "@/plugins/vuetify";
import Individual from "@/views/Individual";

describe("Individual", () => {
  const mockedQuery = [
    {
      mk: "abcde123456",
      isLocked: false,
      profile: {
        name: "John Doe",
        email: "johndoe@example.com",
        isBot: false,
        gender: null,
        country: null,
      },
      identities: [
        {
          name: "John Doe",
          source: "github",
          uuid: "4c8620c3d43e2873dd9d9a8748e0afadeef9d53a",
          username: "johndoe",
          email: "johndoe@example.com",
        },
        {
          source: "github",
          uuid: "9a6e9ca58185a7f5579bca8ab434cb58cfc79f15",
          username: "johndoe",
        },
        {
          source: "github",
          uuid: "5579bca8ab4349a6e9ca58185a7fcb58cfc79f15",
          username: "johndoe",
          email: "johndoe@example.com",
        },
        {
          source: "git",
          email: "johndoe@example.com",
          uuid: "f0422fed699c5a1096808272ae51c69f37f7dd29",
        },
      ],
      enrollments: [],
      matchRecommendationSet: [],
    },
  ];

  const mountFunction = () =>
    mount(VApp, {
      slots: {
        default: h(Individual),
      },
      global: {
        mocks: {
          $apollo: () => {},
          $store: { getters: { workspace: [] } },
          $route: { params: "bcde123456" },
        },
        plugins: [vuetify],
        stubs: ["routerLink"],
      },
    });

  test("Renders link to GitHub profile", async () => {
    const wrapper = mountFunction();
    const component = wrapper.getComponent(Individual);
    component.vm.updateIndividual(mockedQuery);

    await nextTick();

    const link = wrapper.find('[data-profile-link="github"]');

    expect(link.exists()).toBe(true);
    expect(link.text()).toBe("johndoe");
    expect(link.attributes("href")).toBe("http://github.com/johndoe");
  });

  test("Does not render duplicated links", async () => {
    const wrapper = mountFunction();
    const component = wrapper.getComponent(Individual);
    component.vm.updateIndividual(mockedQuery);

    await nextTick();

    expect(wrapper.findAll('[data-profile-link="github"]')).toHaveLength(1);
  });

  test("Matches snapshot", async () => {
    const wrapper = mountFunction();
    const component = wrapper.getComponent(Individual);
    component.vm.updateIndividual(mockedQuery);

    await nextTick();

    expect(wrapper.element).toMatchSnapshot();
  });
});
