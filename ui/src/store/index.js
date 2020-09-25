import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    selectedIndividuals: [],
    selectedIndividual: {
      uuid: undefined,
      selected: undefined
    }
  },
  mutations: {
    addIndividual(state, individual) {
      const selectedIndex = state.selectedIndividuals.findIndex(
        selectedIndividual => selectedIndividual === individual
      );

      if (selectedIndex !== -1) {
        state.selectedIndividuals.splice(selectedIndex, 1);
        state.selectedIndividual = state.selectedIndividual = {
          uuid: individual,
          selected: false
        };
      } else {
        state.selectedIndividuals.push(individual);
        state.selectedIndividual = {
          uuid: individual,
          selected: true
        };
      }
    }
  },
  getters: {
    selectedIndividual(state) {
      return state.selectedIndividual;
    },
    selectedIndividuals(state) {
      return state.selectedIndividuals;
    }
  },
  actions: {},
  modules: {}
});
