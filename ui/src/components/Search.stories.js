import { storiesOf } from "@storybook/vue";

import Search from "./Search.vue";

export default {
  title: "Search",
  excludeStories: /.*Data$/
};

const searchTemplate = `
  <div width="380" class="mx-auto">
    <search />
  </div>
`;

export const Default = () => ({
  components: { Search },
  template: searchTemplate
});
