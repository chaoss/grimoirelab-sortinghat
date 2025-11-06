import { createStore } from "vuex";
import Cookies from "js-cookie";
import router from "../router";
import workspaceStore from "./workspace";

export const store = createStore({
  state: {
    user: Cookies.get("sh_user"),
  },
  mutations: {
    loginUser(state, user) {
      state.user = user;
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.user,
    user: (state) => state.user,
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
    logout({ commit }, redirect) {
      commit("loginUser", undefined);
      Cookies.remove("sh_user");
      router.push({ name: "Login", query: redirect });
    },
  },
  modules: {
    workspace: workspaceStore,
  },
});
