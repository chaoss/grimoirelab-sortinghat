import { createStore } from "vuex";
import Cookies from "js-cookie";
import router from "../router";

export const store = createStore({
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
      const pathname = "/api/login/";
      let origin = process.env.BASE_URL.replace(/\/$/, "");

      if (process.env.VUE_APP_API_URL) {
        origin = new URL(process.env.VUE_APP_API_URL).origin.replace(/\/$/, "");
      }

      const url = `${origin}${pathname}`;
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
    logout({ commit }) {
      commit("loginUser", undefined);
      Cookies.remove("sh_user");
      router.push("/login");
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
