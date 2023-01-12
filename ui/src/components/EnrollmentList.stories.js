import EnrollmentList from "./EnrollmentList.vue";

export default {
  title: "EnrollmentList",
  excludeStories: /.*Data$/,
};

const template = `
  <enrollment-list
    :enrollments="enrollments"
    :compact="compact"
    :isLocked="false"
  />`;

const enrollments = [
  {
    start: "1892-09-01T00:00:00+00:00",
    end: "1997-06-30T00:00:00+00:00",
    group: {
      name: "Hogwarts",
      type: "organization",
    },
  },
  {
    start: "1892-09-01T00:00:00+00:00",
    end: "1899-06-02T00:00:00+00:00",
    group: {
      name: "Gryffindor",
      type: "team",
      parentOrg: { name: "Hogwarts" },
    },
  },
  {
    start: "1910-09-01T00:00:00+00:00",
    end: "1969-06-01T00:00:00+00:00",
    group: {
      name: "Transfiguration department",
      type: "team",
      parentOrg: { name: "Hogwarts" },
    },
  },
  {
    start: "1970-10-01T00:00:00+00:00",
    end: "1997-06-30T00:00:00+00:00",
    group: {
      name: "Order of the Phoenix",
      type: "organization",
    },
  },
  {
    start: "1991-01-01T00:00:00+00:00",
    end: "1995-04-02T00:00:00+00:00",
    group: {
      name: "International Confederation of Wizards",
      type: "organization",
    },
  },
];

export const Default = () => ({
  components: { EnrollmentList },
  template: template,
  data: () => ({
    compact: false,
    enrollments: enrollments,
  }),
});

export const Compact = () => ({
  components: { EnrollmentList },
  template: template,
  data: () => ({
    compact: true,
    enrollments: enrollments,
  }),
});
