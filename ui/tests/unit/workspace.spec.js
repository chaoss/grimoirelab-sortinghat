import { shallowMount } from "@vue/test-utils";
import vuetify from "@/plugins/vuetify";
import Workspace from "@/components/WorkSpace";

describe("Workspace", () => {
  test("Updates the list of individuals", async () => {
    const wrapper = shallowMount(Workspace, {
      global: {
        plugins: [vuetify],
        renderStubDefaultSlot: true,
      },
      props: {
        individuals: [
          {
            name: "John Smith",
            uuid: "0010a5211c03c46d340ada434b9f5b5072a8d491",
            email: "jsmith@example.com",
            isLocked: false,
            sources: [
              {
                icon: "mdi-slack",
                name: "slack",
              },
            ],
            identities: [
              {
                name: "slack",
                identities: [
                  {
                    source: "slack",
                    email: "jsmith@example.com",
                  },
                ],
              },
            ],
          },
          {
            name: "J. Smith",
            uuid: "005b3e8599cc6f64259b7210a5380f113cfd84d7",
            email: "jsmith@example.com",
            isLocked: false,
            sources: [
              {
                icon: "mdi-github",
                name: "github",
              },
            ],
            identities: [
              {
                name: "github",
                identities: [
                  {
                    source: "github",
                    email: "jsmith@example.com",
                  },
                ],
              },
            ],
          },
        ],
        enroll: () => {},
        mergeItems: () => {},
        moveItem: () => {},
      },
    });

    expect(wrapper.html()).toContain("John Smith");
    expect(wrapper.html()).toContain("J. Smith");

    await wrapper.setProps({
      individuals: [
        {
          name: "Jane Doe",
          uuid: "00327ebd3e7ea358f198a4218b508c55e5dbd488",
          email: "jdoe@example.com",
          isLocked: false,
          sources: [
            {
              icon: "mdi-git",
              name: "git",
            },
          ],
          identities: [
            {
              name: "git",
              identities: [
                {
                  source: "git",
                  email: "jdoe@example.com",
                },
              ],
            },
          ],
        },
      ],
    });

    expect(wrapper.html()).toContain("Jane Doe");
    expect(wrapper.html()).not.toContain("John Smith");
    expect(wrapper.html()).not.toContain("J. Smith");

    await wrapper.setProps({
      individuals: [],
    });

    expect(wrapper.html()).not.toContain("John Smith");
    expect(wrapper.html()).not.toContain("J. Smith");
    expect(wrapper.html()).not.toContain("Jane Doe");
  });
});
