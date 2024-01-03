import Vue from "vue";
import Vuex from "vuex";
import Cookies from "js-cookie";

Vue.use(Vuex);

export default new Vuex.Store({
  state: {
    user: Cookies.get("sh_user"),
    workspace: JSON.parse(localStorage.getItem("sh_workspace")) || [],
  },
  mutations: {
    loginUser(state, user) {
      state.user = user;
    },
    setWorkspace(state, workspaceData) {
      state.workspace = workspaceData;
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.user,
    user: (state) => state.user,
    workspace: (state) => state.workspace,
  },
  actions: {
    async login({ commit }, { username, password }) {
      const csrftoken = Cookies.get("csrftoken");
      let url = "/api/login/";

      if (process.env.VUE_APP_API_URL) {
        const origin = new URL(process.env.VUE_APP_API_URL).origin;
        url = `${origin}${url}`;
      }

      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      if (response.status === 200) {
        Cookies.set("sh_user", username, { sameSite: "strict", expires: 14 });
        commit("loginUser", username);

        return response;
      } else {
        const error = await response.json();
        throw new Error(error.errors);
      }
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
    togglePin({ commit, state }, uuid) {
      const index = state.workspace.indexOf(uuid);
      const workspace = state.workspace;
      if (index === -1) {
        workspace.push(uuid);
      } else {
        workspace.splice(index, 1);
      }
      commit("setWorkspace", workspace);
      localStorage.setItem("sh_workspace", JSON.stringify(workspace));
    },
  },
  modules: {},
});
