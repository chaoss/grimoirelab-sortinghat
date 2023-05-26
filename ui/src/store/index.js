import Vue from "vue";
import Vuex from "vuex";
import Cookies from "js-cookie";
import { tokenAuth } from "../apollo/mutations";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    token: Cookies.get("sh_authtoken"),
    user: Cookies.get("sh_user"),
    workspace: JSON.parse(localStorage.getItem("sh_workspace")),
    tourViewed: Cookies.get("sh_tour:viewed"),
  },
  mutations: {
    setToken(state, token) {
      state.token = token;
    },
    loginUser(state, user) {
      state.user = user;
    },
    setWorkspace(state, workspaceData) {
      state.workspace = workspaceData;
    },
    setTourViewed(state, value) {
      state.tourViewed = value;
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.token,
    user: (state) => state.user,
    workspace: (state) => state.workspace,
    shouldShowTour: (state) => !state.tourViewed,
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
        Cookies.set("sh_authtoken", token, { sameSite: "strict" });
        commit("loginUser", authDetails.username);
        Cookies.set("sh_user", authDetails.username, { sameSite: "strict" });
        return token;
      }
      return response;
    },
    saveWorkspace({ commit }, workspaceData) {
      const uuids = workspaceData.map((individual) => individual.uuid);
      localStorage.setItem("sh_workspace", JSON.stringify(uuids));
      commit("setWorkspace", uuids);
    },
    emptyWorkspace({ commit }) {
      localStorage.setItem("sh_workspace", JSON.stringify([]));
      commit("setWorkspace", []);
    },
    setTourViewed({ commit }, value) {
      Cookies.set("sh_tour:viewed", value, {
        expires: 400,
        sameSite: "strict",
      });
      commit("setTourViewed", value);
    },
  },
  modules: {},
});
