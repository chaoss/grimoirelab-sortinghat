import IndividualCard from "./IndividualCard.vue";

export default {
  title: "IndividualCard",
  excludeStories: /.*Data$/,
};

const individualCardTemplate = `
  <individual-card
    :name="name"
    :email="email"
    :sources="sources"
    :uuid="uuid"
    :identities="identities"
    :enrollments="enrollments"
    :is-highlighted="isHighlighted"
    :is-locked="isLocked"
    :closable="closable"
    :selectable="selectable"
    :is-selected="isSelected"
    />`;

export const Default = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});
export const SingleInitial = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Voldemort",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "voldemort@example.net",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});
export const NoName = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [
        {
          name: "GitLab",
          icon: "mdi-gitlab",
          identities: [
            {
              name: "",
              source: "GitLab",
              email: "triddle@example.net",
              uuid: "03b3428ee",
              username: "triddle",
            },
          ],
        },
      ],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});
export const Sources = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [
        { name: "git", icon: "mdi-git" },
        { name: "github", icon: "mdi-github" },
        { name: "gitlab", icon: "mdi-gitlab" },
        { name: "Other sources", icon: "mdi-account-multiple" },
      ],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    isHighlighted: {
      default: false,
    },
    identities: {
      default: () => [
        {
          name: "GitLab",
          icon: "mdi-gitlab",
          identities: [
            {
              name: "Tom Marvolo Riddle",
              source: "GitLab",
              email: "triddle@example.net",
              uuid: "03b3428ee",
              username: "triddle",
            },
          ],
        },
        {
          name: "GitHub",
          icon: "mdi-github",
          identities: [
            {
              uuid: "808b18",
              name: "Voldemort",
              email: "-",
              username: "voldemort",
              source: "github",
            },
          ],
        },
        {
          name: "git",
          icon: "mdi-git",
          identities: [
            {
              uuid: "006afa",
              name: "Tom Marvolo Riddle",
              email: "triddle@example.net",
              username: "triddle",
              source: "git",
            },
            {
              uuid: "abce32",
              name: "voldemort",
              email: "voldemort@example.net",
              username: "-",
              source: "git",
            },
          ],
        },
      ],
    },
    enrollments: {
      default: () => [],
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});
export const Organization = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: true,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    isHighlighted: {
      default: false,
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [
        {
          group: {
            name: "Slytherin",
            id: "2",
          },
          start: "1938-09-01T00:00:00+00:00",
          end: "1998-05-02T00:00:00+00:00",
        },
        {
          group: {
            name: "Hogwarts School of Witchcraft and Wizardry",
            id: "1",
          },
          start: "1938-09-01",
          end: "1945-06-02T00:00:00+00:00",
        },
      ],
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});

export const Highlighted = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    isHighlighted: {
      default: true,
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});

export const SourcesAndOrganization = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [
        { name: "git", icon: "mdi-git" },
        { name: "github", icon: "mdi-github" },
        { name: "gitlab", icon: "mdi-gitlab" },
        { name: "Other sources", icon: "mdi-account-multiple" },
      ],
    },
    isLocked: {
      default: true,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [
        {
          name: "GitLab",
          icon: "mdi-gitlab",
          identities: [
            {
              name: "Tom Marvolo Riddle",
              source: "GitLab",
              email: "triddle@example.net",
              uuid: "03b3428ee",
              username: "triddle",
            },
          ],
        },
        {
          name: "GitHub",
          icon: "mdi-github",
          identities: [
            {
              uuid: "808b18",
              name: "Voldemort",
              email: "-",
              username: "voldemort",
              source: "github",
            },
          ],
        },
        {
          name: "git",
          icon: "mdi-git",
          identities: [
            {
              uuid: "006afa",
              name: "Tom Marvolo Riddle",
              email: "triddle@example.net",
              username: "triddle",
              source: "git",
            },
            {
              uuid: "abce32",
              name: "voldemort",
              email: "voldemort@example.net",
              username: "-",
              source: "git",
            },
          ],
        },
      ],
    },
    enrollments: {
      default: () => [
        {
          group: {
            name: "Slytherin",
            id: "2",
          },
          start: "1938-09-01T00:00:00+00:00",
          end: "1998-05-02T00:00:00+00:00",
        },
        {
          group: {
            name: "Hogwarts School of Witchcraft and Wizardry",
            id: "1",
          },
          start: "1938-09-01",
          end: "1945-06-02T00:00:00+00:00",
        },
      ],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});

export const Gravatar = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Santiago Dueñas",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "sduenas@bitergia.com",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});

export const Closable = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: true,
    },
    selectable: {
      default: false,
    },
    isSelected: {
      default: false,
    },
  },
});

export const Selectable = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: true,
    },
    isSelected: {
      default: false,
    },
  },
});

export const Selected = () => ({
  components: { IndividualCard },
  template: individualCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle",
    },
    sources: {
      default: () => [],
    },
    isLocked: {
      default: false,
    },
    uuid: {
      default: "10f546",
    },
    email: {
      default: "triddle@example.net",
    },
    identities: {
      default: () => [],
    },
    enrollments: {
      default: () => [],
    },
    isHighlighted: {
      default: false,
    },
    closable: {
      default: false,
    },
    selectable: {
      default: true,
    },
    isSelected: {
      default: true,
    },
  },
});
