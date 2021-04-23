import Router from "vue-router";
import store from "../store";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: () => import("../views/Dashboard"),
    meta: { requiresAuth: true, title: "Sorting Hat" }
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login"),
    meta: { title: "Log in - Sorting Hat" }
  },
  {
    path: "/search-help",
    name: "SearchHelp",
    component: () => import("../views/SearchHelp"),
    meta: { title: "Search Help - Sorting Hat" }
  },
  {
    path: "/jobs",
    name: "Jobs",
    component: () => import("../views/Jobs"),
    meta: { title: "Jobs - Sorting Hat" }
  }
];

const router = new Router({
  mode: "history",
  routes
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated;
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      next({
        path: "/login"
      });
    } else {
      next();
    }
  } else if (to.path === "/login" && isAuthenticated) {
    next({
      path: "/"
    });
  } else {
    next();
  }
});

export default router;
