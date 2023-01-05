import Search from "./Search.vue";

export default {
  title: "Search",
  excludeStories: /.*Data$/
};

const searchTemplate = `
  <div class="ma-5">
    <search
      :valid-filters="validFilters"
      :filter-selector="filterSelector"
      :order-selector="orderSelector"
    />
  </div>
`;

export const Default = () => ({
  components: { Search },
  template: searchTemplate,
  data: () => ({
    validFilters: [],
    filterSelector: false,
    orderSelector: false
  })
});

export const filterSelector = () => ({
  components: { Search },
  template: searchTemplate,
  data: () => ({
    validFilters: [
      {
        filter: "country",
        type: "string"
      },
      {
        filter: "isBot",
        type: "boolean"
      }
    ],
    filterSelector: true,
    orderSelector: false
  })
});

export const orderSelector = () => ({
  components: { Search },
  template: searchTemplate,
  data: () => ({
    orderSelector: true,
    validFilters: [],
    filterSelector: false
  })
});
