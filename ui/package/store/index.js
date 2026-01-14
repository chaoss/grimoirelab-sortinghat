import { createStore } from "vuex";
import workspaceStore from "../../src/store/workspace"

export const store = createStore({
  modules: {
    workspace: workspaceStore
  }
})
