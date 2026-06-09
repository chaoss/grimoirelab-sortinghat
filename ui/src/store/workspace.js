const workspaceStore = {
  state: () => ({
    workspace: JSON.parse(localStorage.getItem("sh_workspace")) || [],
  }),
  mutations: {
    setWorkspace(state, workspaceData) {
      state.workspace = workspaceData;
    },
  },
  getters: {
    workspace: (state) => state.workspace,
  },
  actions: {
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
};

export default workspaceStore;
