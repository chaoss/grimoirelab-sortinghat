import { storiesOf } from "@storybook/vue";

import Search from "./Search.vue";

export default {
  title: "Search",
  excludeStories: /.*Data$/
};

const searchTemplate = `
  <div class="mx-auto mt-5">
    <search />
  </div>
`;

export const Default = () => ({
  components: { Search },
  template: searchTemplate
});
