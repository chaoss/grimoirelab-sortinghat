export default [
  {
    path: "",
    name: "Dashboard",
    component: () => import("../../src/views/Dashboard.vue"),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "organization/:name",
    name: "Organization",
    component: () => import("../../src/views/Organization.vue"),
    meta: {
      breadcrumb: {
        title: '',
        param: 'name'
      },
      requiresAuth: true,
    }
  },
  {
    path: "individual/:mk",
    name: "Individual",
    component: () => import("../../src/views/Individual.vue"),
    meta: {
      breadcrumb: {
        title: 'Identity',
        param: 'mk'
      },
      requiresAuth: true,
    }
  },
  {
    path: "/search-help",
    name: "SearchHelp",
    component: () => import("../../src/views/SearchHelp.vue"),
    meta: { requiresAuth: true },
  },
]
