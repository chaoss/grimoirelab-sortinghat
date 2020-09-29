<template>
  <IndividualsGrid :individuals="individuals.entities" class="grid" />
</template>

<script>
import IndividualsGrid from "./IndividualsGrid.vue";
export default {
  name: "individualsdata",
  components: {
    IndividualsGrid
  },
  data: () => ({
    individuals: {
      entities: []
    }
  }),
  props: {
    getindividuals: {
      type: Object,
      required: true
    }
  },
  async created() {
    let response = await this.getindividuals.query(this.$apollo, 50);
    if (response) {
      this.individuals = response.data.individuals;
    }
  },
  mounted() {
    this.scroll();
  },
  methods: {
    scroll() {
      window.onscroll = async () => {
        let bottomOfWindow =
          document.documentElement.scrollTop + window.innerHeight ===
          document.documentElement.offsetHeight;

        if (bottomOfWindow) {
          let response = await this.getindividuals.query(this.$apollo, 50);
          if (response) {
            this.individuals.entities = [
              ...this.individuals.entities,
              ...response.data.individuals.entities
            ];
          }
        }
      };
    }
  }
};
</script>
<style scoped>
.grid {
  align-self: start;
  margin-right: 5px;
  margin-top: 64px;
}
</style>
