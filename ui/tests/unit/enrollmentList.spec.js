import { shallowMount } from "@vue/test-utils";
import vuetify from "@/plugins/vuetify";
import EnrollmentList from "@/components/EnrollmentList";

describe("EnrollmentList component", () => {
  const mountFunction = (options) => {
    return shallowMount(EnrollmentList, {
      global: {
        plugins: [vuetify],
      },
      propsData: { enrollments: [] },
      ...options,
    });
  };

  test("Groups enrollments by organization", () => {
    const wrapper = mountFunction();
    const enrollments = [
      {
        start: "2000-01-01T00:00:00+00:00",
        end: "2004-01-02T00:00:00+00:00",
        group: {
          name: "Organization 1",
          type: "organization",
        },
      },
      {
        start: "2006-01-01T00:00:00+00:00",
        end: "2008-01-02T00:00:00+00:00",
        group: {
          name: "Organization 1",
          type: "organization",
        },
      },
      {
        start: "2010-01-01T00:00:00+00:00",
        end: "2012-01-02T00:00:00+00:00",
        group: {
          name: "Organization 1",
          type: "organization",
        },
      },
      {
        start: "2004-01-01T00:00:00+00:00",
        end: "2006-01-02T00:00:00+00:00",
        group: {
          name: "Organization 2",
          type: "organization",
          parentOrg: null,
        },
      },
    ];

    const groupedEnrollments = wrapper.vm.groupEnrollments(enrollments);
    expect(Object.keys(groupedEnrollments).length).toBe(2);

    const organization1 = groupedEnrollments["Organization 1"];
    expect(organization1.enrollments.length).toBe(3);

    const organization2 = groupedEnrollments["Organization 2"];
    expect(organization2.enrollments.length).toBe(1);
  });

  test("Groups team enrollments by their parent organization", () => {
    const wrapper = mountFunction();
    const enrollments = [
      {
        start: "2000-01-01T00:00:00+00:00",
        end: "2004-01-02T00:00:00+00:00",
        group: {
          name: "Organization 1",
          type: "organization",
          parentOrg: null,
        },
      },
      {
        start: "2000-01-01T00:00:00+00:00",
        end: "2002-01-01T00:00:00+00:00",
        group: {
          name: "Team 1",
          type: "team",
          parentOrg: { name: "Organization 1" },
        },
      },
      {
        start: "2002-01-01T00:00:00+00:00",
        end: "2004-01-01T00:00:00+00:00",
        group: {
          name: "Team 2",
          type: "team",
          parentOrg: { name: "Organization 1" },
        },
      },
      {
        start: "2005-01-01T00:00:00+00:00",
        end: "2007-01-02T00:00:00+00:00",
        group: {
          name: "Organization 2",
          type: "organization",
          parentOrg: null,
        },
      },
      {
        start: "2005-01-01T00:00:00+00:00",
        end: "2007-01-01T00:00:00+00:00",
        group: {
          name: "Team 3",
          type: "team",
          parentOrg: { name: "Organization 2" },
        },
      },
    ];

    const groupedEnrollments = wrapper.vm.groupEnrollments(enrollments);
    expect(Object.keys(groupedEnrollments).length).toBe(2);

    const organization1 = groupedEnrollments["Organization 1"];
    expect(organization1.enrollments.length).toBe(1);
    expect(organization1.enrollments[0].start).toBe(
      "2000-01-01T00:00:00+00:00"
    );
    expect(organization1.enrollments[0].end).toBe("2004-01-02T00:00:00+00:00");
    expect(organization1.teams.length).toBe(2);

    const team1 = organization1.teams[0];
    expect(team1.group.name).toBe("Team 1");
    expect(team1.start).toBe("2000-01-01T00:00:00+00:00");
    expect(team1.end).toBe("2002-01-01T00:00:00+00:00");

    const team2 = organization1.teams[1];
    expect(team2.group.name).toBe("Team 2");
    expect(team2.start).toBe("2002-01-01T00:00:00+00:00");
    expect(team2.end).toBe("2004-01-01T00:00:00+00:00");

    const organization2 = groupedEnrollments["Organization 2"];
    expect(organization2.enrollments.length).toBe(1);
    expect(organization2.enrollments[0].start).toBe(
      "2005-01-01T00:00:00+00:00"
    );
    expect(organization2.enrollments[0].end).toBe("2007-01-02T00:00:00+00:00");
    expect(organization2.teams.length).toBe(1);

    const team3 = organization2.teams[0];
    expect(team3.group.name).toBe("Team 3");
    expect(team3.start).toBe("2005-01-01T00:00:00+00:00");
    expect(team3.end).toBe("2007-01-01T00:00:00+00:00");
  });
});
