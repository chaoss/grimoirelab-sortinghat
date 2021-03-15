import IndividualEntry from "./IndividualEntry.vue";

export default {
  title: "IndividualEntry",
  excludeStories: /.*Data$/
};

const individualEntryTemplate = `
  <v-data-table
    hide-default-header
    hide-default-footer
    :headers="headers"
    :items="items"
    :expanded.sync="expanded"
    item-key="name"
  >
    <template v-slot:item="{ item, expand, isExpanded }">
      <individual-entry
        :name="item.name"
        :organization="item.organization"
        :email="item.email"
        :sources="item.sources"
        :is-expanded="isExpanded"
        :is-locked="item.isLocked"
        :is-bot="item.isBot"
        :uuid="item.uuid"
        :is-highlighted="item.isHighlighted"
        @expand="expand(!isExpanded)"
      />
    </template>
    <template v-slot:expanded-item="{ item, expansion }">
      Expanded content {{ expansion }}
    </template>
  </v-data-table>
`;

export const Default = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const NoEmail = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const NoOrganization = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const NoName = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "",
        organization: "",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const SingleInital = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Voldemort",
        organization: "Death Eaters",
        email: "lord.voldemort@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const Locked = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: true,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const Bot = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: true,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const BotAndLocked = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: true,
        isBot: true,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});

export const Highlighted = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: true
      }
    ],
    expanded: []
  })
});

export const Gravatar = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" }
    ],
    items: [
      {
        name: "Santiago Dueñas",
        email: "sduenas@bitergia.com",
        sources: [{ name: "git", icon: "mdi-git" }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false
      }
    ],
    expanded: []
  })
});
