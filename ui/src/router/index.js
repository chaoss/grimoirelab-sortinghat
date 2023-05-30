import Router from "vue-router";
import store from "../store";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: () => import("../views/Dashboard"),
    meta: { requiresAuth: true, showTour: true, title: "Sorting Hat" },
  },
  {
    path: "/individual/:mk",
    name: "Individual",
    component: () => import("../views/Individual"),
    meta: { requiresAuth: true, title: "Sorting Hat" },
  },
  {
    path: "/change-password",
    name: "ChangePassword",
    component: () => import("../views/ChangePassword"),
    meta: { requiresAuth: true, title: "Password change - Sorting Hat" },
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login"),
    meta: { title: "Log in - Sorting Hat" },
  },
  {
    path: "/search-help",
    name: "SearchHelp",
    component: () => import("../views/SearchHelp"),
    meta: { title: "Search Help - Sorting Hat" },
  },
  {
    path: "/jobs",
    name: "Jobs",
    component: () => import("../views/Jobs"),
    meta: { title: "Jobs - Sorting Hat" },
  },
  {
    path: "/import-identities",
    name: "ImportIdentities",
    component: () => import("../views/ImportIdentities"),
    meta: { requiresAuth: true, title: "Import identities - Sorting Hat" },
  },
  {
    path: "/organization/:name",
    name: "Organization",
    component: () => import("../views/Organization"),
    meta: { requiresAuth: true, title: "Sorting Hat" },
  },
  {
    path: "/product-tour",
    name: "ProductTour",
    component: () => import("../views/ProductTour"),
    meta: { requiresAuth: true, title: "Sorting Hat" },
  },
];

const router = new Router({
  mode: "history",
  base: process.env.NODE_ENV === "production" ? "/identities/" : null,
  routes,
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated;
  const showTour =
    to.matched.some((record) => record.meta.showTour) &&
    store.getters.shouldShowTour;

  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      next({
        path: "/login",
      });
    } else if (showTour) {
      next({
        path: "/product-tour",
      });
    } else {
      next();
    }
  } else if (to.path === "/login" && isAuthenticated) {
    next({
      path: "/",
    });
  } else {
    next();
  }
});

export default router;
