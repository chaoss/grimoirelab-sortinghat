import { storiesOf } from "@storybook/vue";

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
      { value: 'name' },
      { value: 'email' },
      { value: 'sources' },
      { value: 'actions' }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [ "git", "others" ],
        isLocked: false
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
      { value: 'name' },
      { value: 'email' },
      { value: 'sources' },
      { value: 'actions' }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "",
        sources: [ "git", "others" ],
        isLocked: false
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
      { value: 'name' },
      { value: 'email' },
      { value: 'sources' },
      { value: 'actions' }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "",
        email: "triddle@example.com",
        sources: [ "git", "others" ],
        isLocked: false
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
      { value: 'name' },
      { value: 'email' },
      { value: 'sources' },
      { value: 'actions' }
    ],
    items: [
      {
        name: "Voldemort",
        organization: "Death Eaters",
        email: "lord.voldemort@example.com",
        sources: [ "git", "others" ],
        isLocked: false
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
      { value: 'name' },
      { value: 'email' },
      { value: 'sources' },
      { value: 'actions' }
    ],
    items: [
      {
        name: "Tom Marvolo Riddle",
        organization: "Slytherin",
        email: "triddle@example.com",
        sources: [ "git", "others" ],
        isLocked: true
      }
    ],
    expanded: []
  })
});
