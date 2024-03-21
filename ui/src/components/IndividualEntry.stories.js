import IndividualEntry from "./IndividualEntry.vue";

export default {
  title: "IndividualEntry",
  excludeStories: /.*Data$/,
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
    <template
      v-slot:item="{
        item,
        toggleExpand,
        isExpanded,
        isSelected,
        internalItem,
        toggleSelect,
      }">
      <individual-entry
        :name="item.name"
        :organization="item.organization"
        :email="item.email"
        :sources="item.sources"
        :is-expanded="isExpanded(internalItem)"
        :is-locked="item.isLocked"
        :is-bot="item.isBot"
        :uuid="item.uuid"
        :is-highlighted="item.isHighlighted"
        :is-expandable="expandable"
        :is-selected="isSelected([internalItem])"
        @expand="toggleExpand(internalItem)"
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
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const NoEmail = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const NoOrganization = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const NoName = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "",
        organization: "",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const SingleInital = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Voldemort",
        organization: "Death Eaters",
        email: "lord.voldemort@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const Locked = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: true,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const Bot = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: true,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const BotAndLocked = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: true,
        isBot: true,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const Highlighted = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: true,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const Gravatar = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Santiago Dueñas",
        email: "sduenas@bitergia.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: false,
  }),
});

export const Expandable = () => ({
  components: { IndividualEntry },
  template: individualEntryTemplate,
  data: () => ({
    headers: [
      { value: "name" },
      { value: "email" },
      { value: "sources" },
      { value: "actions" },
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [{ name: "git", icon: "mdi-git", count: 2 }],
        isLocked: false,
        isBot: false,
        uuid: "03b3428ee",
        isHighlighted: false,
      },
    ],
    expanded: [],
    expandable: true,
  }),
});
