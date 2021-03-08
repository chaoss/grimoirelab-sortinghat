import Search from "./Search.vue";

export default {
  title: "Search",
  excludeStories: /.*Data$/
};

const searchTemplate = `
  <div class="ma-5">
    <search :valid-filters="validFilters" />
  </div>
`;

export const Default = () => ({
  components: { Search },
  template: searchTemplate,
  data: () => ({
    validFilters: []
  })
});
