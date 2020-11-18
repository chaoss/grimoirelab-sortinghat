import Vue from "vue";
import Vuex from "vuex";
import Cookies from "js-cookie";
import { tokenAuth } from "../apollo/mutations";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    token: Cookies.get("sh_authtoken"),
    user: Cookies.get("sh_user"),
    selectedIndividuals: [],
    selectedIndividual: {
      uuid: undefined,
      selected: undefined
    }
  },
  mutations: {
    setToken(state, token) {
      state.token = token;
    },
    loginUser(state, user) {
      state.user = user;
    },
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
    isAuthenticated: state => !!state.token,
    user: state => state.user,
    selectedIndividual(state) {
      return state.selectedIndividual;
    },
    selectedIndividuals(state) {
      return state.selectedIndividuals;
    }
  },
  actions: {
    async login({ commit }, authDetails) {
      const response = await tokenAuth(
        authDetails.apollo,
        authDetails.username,
        authDetails.password
      );
      if (response && !response.errors) {
        const token = response.data.tokenAuth.token;
        commit("setToken", token);
        Cookies.set("sh_authtoken", token, { secure: true });
        commit("loginUser", authDetails.username);
        Cookies.set("sh_user", authDetails.username, { secure: true });
        return token;
      }
      return response;
    }
  },
  modules: {}
});
