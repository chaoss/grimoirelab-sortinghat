import { storiesOf } from "@storybook/vue";

import OrganizationEntry from "./OrganizationEntry.vue";

export default {
  title: "OrganizationEntry",
  excludeStories: /.*Data$/
};

const organizationEntryTemplate = `
<v-data-table
  hide-default-header
  hide-default-footer
  :headers="headers"
  :items="items"
  item-key="name"
>
  <template v-slot:item="{ item }">
    <organization-entry :name="item.name" :enrollments="item.enrollments" />
  </template>
</v-data-table>
`;

export const Default = () => ({
  components: { OrganizationEntry },
  template: organizationEntryTemplate,
  data: () => ({
    headers: [
      { value: 'name' },
      { value: 'enrollments' }
    ],
    items: [
      {
        name: "Hogwarts School of Witchcraft and Wizardry",
        enrollments: 280
      }
    ],
    expanded: []
  })
});
