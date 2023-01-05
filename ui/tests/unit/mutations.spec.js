import { shallowMount } from "@vue/test-utils";
import Vue from "vue";
import Vuetify from "vuetify";
import IndividualsTable from "@/components/IndividualsTable";
import Login from "@/views/Login";
import OrganizationsTable from "@/components/OrganizationsTable";
import ProfileModal from "@/components/ProfileModal";
import * as Mutations from "@/apollo/mutations";
import TeamModal from "@/components/TeamModal";
import Jobs from "@/views/Jobs";

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
  data: {
    unmergeIdentities: {
      uuids: [
        "3db176be6859adac3a454c5377af81b1b7e3f8d8",
        "10982379421b80e13266db011d6e5131dd519016"
      ],
      individuals: [
        {
          profile: {
            name: "Test 11",
            id: "260",
            isBot: false
          },
          identities: [
            {
              name: "Test 11",
              source: "git",
              email: "test11@example.net",
              uuid: "3db176be6859adac3a454c5377af81b1b7e3f8d8",
              username: "tes39"
            }
          ],
          enrollments: []
        },
        {
          profile: {
            name: "Test 4",
            id: "255",
            isBot: false
          },
          identities: [
            {
              name: "Test 4",
              source: "test",
              email: "test4@example.net",
              uuid: "10982379421b80e13266db011d6e5131dd519016",
              username: "test4"
            }
          ],
          enrollments: []
        }
      ]
    }
  }
};

const moveResponse = {
  data: {
    moveIdentity: {
      uuid: "7eb22d2a28e3f450ad4fbe171f156a9fab1d3971",
      individual: {
        isLocked: false,
        identities: [{ source: "git" }, { source: "gitlab" }],
        profile: {
          name: "Test",
          id: "254"
        },
        enrollments: []
      }
    }
  }
};

const enrollResponse = {
  data: {
    enroll: {
      uuid: "4df20c13824ce60c2249a9b947d6c55dc0ba26a4",
      individual: {
        isLocked: false,
        identities: [
          {
            name: "Test",
            source: "git",
            email: "teste@example.net",
            uuid: "4df20c13824ce60c2249a9b947d6c55dc0ba26a4",
            username: "test"
          }
        ],
        profile: {
          name: "Test",
          id: "7"
        },
        enrollments: [
          {
            start: "1900-01-01T00:00:00+00:00",
            end: "2100-01-01T00:00:00+00:00",
            group: {
              name: "Organization"
            }
          }
        ]
      }
    }
  }
};

const addOrganizationResponse = {
  data: {
    addOrganization: {
      organization: {
        name: "Name",
        __typename: "OrganizationType"
      },
      __typename: "AddOrganization"
    }
  }
};

const addTeamResponse = {
  data: {
    addTeam: {
      team: {
        name: "Name",
        __typename: "TeamType"
      },
      __typename: "AddTeam"
    }
  }
};

const paginatedTeams = {
  data: {
    teams: {
      entities: [
        {
          name: "Test 1",
          __typename: "TeamType"
        },
        {
          name: "Test 2",
          __typename: "TeamType"
        }
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        totalResults: 2,
        __typename: "PaginationType"
      },
      __typename: "TeamPaginatedType"
    }
  }
};

const addDomainResponse = {
  data: {
    addDomain: {
      domain: {
        domain: "domain.com",
        organization: {
          name: "Organization"
        }
      }
    }
  }
};

const addIdentityResponse = {
  data: {
    addIdentity: {
      uuid: "002bad315c34120cdfa2b1e26b3ca88ce36bc183",
      __typename: "AddIdentity"
    }
  }
};

const tokenResponse = {
  data: {
    tokenAuth: {
      token: "eyJ0eXAiOiJKV1QiL"
    }
  }
};

const withdrawResponse = {
  data: {
    withdraw: {
      uuid: "4df20c13824ce60c2249a9b947d6c55dc0ba26a4"
    }
  }
};

const deleteOrganizationResponse = {
  data: {
    deleteOrganization: {
      organization: {
        name: "Organization",
        __typename: "OrganizationType"
      },
      __typename: "DeleteOrganization"
    }
  }
};

const updateEnrollmentResponse = {
  data: {
    updateEnrollment: {
      uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
      individual: {
        enrollments: [
          {
            start: "2020-11-01T00:00:00+00:00",
            end: "2020-12-24T00:00:00+00:00",
            group: {
              name: "Organization",
              __typename: "GroupType"
            },
            __typename: "EnrollmentType"
          }
        ],
        __typename: "IndividualType"
      },
      __typename: "UpdateEnrollment"
    }
  }
};

const affiliateResponse = {
  data: { affiliate: { jobId: "384f26af-aae4-4c73-96af-e0af90a4cdf3" }}
};

const genderizeResponse = {
  data: { genderize: { jobId: "384f26af-aae4-4c73-96af-e0af90a4cdf3" }}
};

const unifyResponse = {
  data: { unify: { jobId: "384f26af-aae4-4c73-96af-e0af90a4cdf3" }}
};

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
        fetchOrganizations: () => {},
        getCountries: () => {},
        lockIndividual: () => {},
        unlockIndividual: () => {},
        withdraw: () => {},
        updateEnrollment: () => {}
      },
      ...options
    });
  };

  test("Mock query for deleteIdentity", async () => {
    const mutate = jest.fn(() => Promise.resolve(deleteResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ deleteItem: mutate });
    const response = await Mutations.deleteIdentity(
      wrapper.vm.$apollo,
      "5f06473815dc415c9861680de8101813d9eb18e8"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for merge", async () => {
    const mutate = jest.fn(() => Promise.resolve(mergeResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ mergeItems: mutate });
    const response = await Mutations.deleteIdentity(
      wrapper.vm.$apollo,
      "5f06473815dc415c9861680de8101813d9eb18e8"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for unmerge", async () => {
    const mutate = jest.fn(() => Promise.resolve(unmergeResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ unmergeItems: mutate });
    const response = await Mutations.unmerge(wrapper.vm.$apollo, [
      "3db176be6859adac3a454c5377af81b1b7e3f8d8",
      "10982379421b80e13266db011d6e5131dd519016"
    ]);

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for moveIdentity", async () => {
    const mutate = jest.fn(() => Promise.resolve(moveResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ moveItem: mutate });
    const response = await Mutations.moveIdentity(
      wrapper.vm.$apollo,
      "5f06473815dc415c9861680de8101813d9eb18e8",
      "7eb22d2a28e3f450ad4fbe171f156a9fab1d3971"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for withdraw", async () => {
    const mutate = jest.fn(() => Promise.resolve(withdrawResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ withdraw: mutate });
    const response = await Mutations.withdraw(
      wrapper.vm.$apollo,
      "4df20c13824ce60c2249a9b947d6c55dc0ba26a4",
      "Organization"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock query for updateEnrollment", async () => {
    const mutate = jest.fn(() => Promise.resolve(updateEnrollmentResponse));
    const wrapper = mountFunction({
      mocks: {
        $apollo: {
          mutate
        }
      }
    });
    await wrapper.setProps({ updateEnrollment: mutate });
    const enrollment = {
      fromDate: "2020-12-03T00:00:00+00:00",
      newFromDate: "2020-11-01T00:00:00.000Z",
      group: "Organization",
      toDate: "2020-12-24T00:00:00+00:00",
      newToDate: "2020-12-24T00:00:00+00:00",
      uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562"
    };
    const response = await Mutations.updateEnrollment(
      wrapper.vm.$apollo,
      enrollment
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("OrganizationsTable", () => {
  test("Mock mutation for enroll", async () => {
    const mutate = jest.fn(() => Promise.resolve(enrollResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        enroll: mutate,
        fetchPage: () => {},
        addDomain: () => {},
        addOrganization: () => {},
        deleteDomain: () => {},
        deleteOrganization: () => {},
        addTeam: () => {},
        deleteTeam: () => {},
        fetchTeams: () => {}
      }
    });

    const response = await Mutations.enroll(
      wrapper.vm.$apollo,
      "4df20c13824ce60c2249a9b947d6c55dc0ba26a4",
      "Organization"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for addOrganization", async () => {
    const mutate = jest.fn(() => Promise.resolve(addOrganizationResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        enroll: mutate,
        fetchPage: () => {},
        addOrganization: mutate,
        addDomain: () => {},
        deleteDomain: () => {},
        deleteOrganization: () => {},
        addTeam: () => {},
        deleteTeam: () => {},
        fetchTeams: () => {}
      }
    });

    const response = await Mutations.addOrganization(
      wrapper.vm.$apollo,
      "Name"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for addDomain", async () => {
    const mutate = jest.fn(() => Promise.resolve(addDomainResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        enroll: () => {},
        fetchPage: () => {},
        addDomain: mutate,
        deleteDomain: () => {},
        addOrganization: () => {},
        deleteOrganization: () => {},
        addTeam: () => {},
        deleteTeam: () => {},
        fetchTeams: () => {}
      }
    });

    const response = await Mutations.addDomain(
      wrapper.vm.$apollo,
      "domain.com",
      "Organization"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for deleteDomain", async () => {
    const mutate = jest.fn(() => Promise.resolve(addDomainResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        enroll: () => {},
        fetchPage: () => {},
        addDomain: () => {},
        deleteDomain: mutate,
        addOrganization: () => {},
        deleteOrganization: () => {},
        addTeam: () => {},
        deleteTeam: () => {},
        fetchTeams: () => {}
      }
    });

    const response = await Mutations.addDomain(
      wrapper.vm.$apollo,
      "domain.com",
      "Organization"
    );
    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for deleteOrganization", async () => {
    const mutate = jest.fn(() => Promise.resolve(deleteOrganizationResponse));
    const wrapper = shallowMount(OrganizationsTable, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        enroll: () => {},
        fetchPage: () => {},
        addDomain: () => {},
        deleteDomain: () => {},
        addOrganization: () => {},
        deleteOrganization: mutate,
        addTeam: () => {},
        deleteTeam: () => {},
        fetchTeams: () => {}
      }
    });

    const response = await Mutations.deleteOrganization(
      wrapper.vm.$apollo,
      "Organization"
    );
    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("ProfileModal", () => {
  test("Mock mutation for addIdentity", async () => {
    const mutate = jest.fn(() => Promise.resolve(addIdentityResponse));
    const wrapper = shallowMount(ProfileModal, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        addIdentity: mutate,
        updateProfile: () => {},
        enroll: () => {},
        getCountries: () => {},
        fetchOrganizations: () => {}
      }
    });

    const response = await Mutations.addIdentity(
      wrapper.vm.$apollo,
      "email@email.com",
      "Name",
      "source",
      "username"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for updateProfile", async () => {
    const mutate = jest.fn(() => Promise.resolve(addIdentityResponse));
    const wrapper = shallowMount(ProfileModal, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        addIdentity: () => {},
        updateProfile: mutate,
        enroll: () => {},
        getCountries: () => {},
        fetchOrganizations: () => {},
      }
    });

    const response = await Mutations.addIdentity(
      wrapper.vm.$apollo,
      {
        gender: "gender",
        isBot: true
      },
      "002bad315c34120cdfa2b1e26b3ca88ce36bc183"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("Login", () => {
  test("Mock mutation for tokenAuth", async () => {
    const mutate = jest.fn(() => Promise.resolve(tokenResponse));
    const wrapper = shallowMount(Login, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      }
    });

    const response = await Mutations.tokenAuth(
      wrapper.vm.$apollo,
      "username",
      "password"
    );

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("TeamModal", () => {
  test("Mock mutation for addTeam", async () => {
    const mutate = jest.fn(() => Promise.resolve(addTeamResponse));
    const wrapper = shallowMount(TeamModal, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        fetchTeams: () => paginatedTeams,
        addTeam: mutate,
        deleteTeam: () => {},
        parent: "Parent Organization"
      }
    });

    const response = await Mutations.addTeam(wrapper.vm.$apollo, "test");

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for deleteTeam", async () => {
    const mutate = jest.fn(() => Promise.resolve(addTeamResponse));
    const wrapper = shallowMount(TeamModal, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      },
      propsData: {
        fetchTeams: () => paginatedTeams,
        addTeam: () => {},
        deleteTeam: mutate,
        parent: "Parent Organization"
      }
    });

    const response = await Mutations.deleteTeam(wrapper.vm.$apollo, "test");

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});

describe("Jobs", () => {
  test("Mock mutation for affiliate", async () => {
    const mutate = jest.fn(() => Promise.resolve(affiliateResponse));
    const wrapper = shallowMount(Jobs, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      }
    });

    await wrapper.vm.affiliate()

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for genderize", async () => {
    const mutate = jest.fn(() => Promise.resolve(genderizeResponse));
    const wrapper = shallowMount(Jobs, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      }
    });

    await wrapper.vm.genderize({
      exclude: false,
      noStrictMatching: true
    });

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });

  test("Mock mutation for unify", async () => {
    const mutate = jest.fn(() => Promise.resolve(unifyResponse));
    const wrapper = shallowMount(Jobs, {
      Vue,
      mocks: {
        $apollo: {
          mutate
        }
      }
    });

    await wrapper.vm.unify({
      criteria: ["name"],
      exclude: false
    });

    expect(mutate).toBeCalled();
    expect(wrapper.element).toMatchSnapshot();
  });
});
