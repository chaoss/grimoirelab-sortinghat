<template>
  <v-app>
    <v-app-bar color="primary" density="compact" flat class="pl-6 pr-6">
      <router-link
        to="/"
        v-slot="{ href, navigate }"
        class="text-decoration-none"
      >
        <h1 :href="href" @click="navigate" class="text-h6 text-white pointer">
          Sorting Hat
        </h1>
      </router-link>

      <v-spacer></v-spacer>
      <div v-if="user && $route.name !== 'Login'">
        <v-btn to="/" flat size="small" color="white" class="mr-2">
          <v-icon size="small" start> mdi-view-dashboard-variant </v-icon>
          Dashboard
        </v-btn>
        <v-btn to="/settings" flat size="small" color="white" class="mr-2">
          <v-icon size="small" start> mdi-cog </v-icon>
          Settings
        </v-btn>
        <v-menu offset-y left>
          <template v-slot:activator="{ props }">
            <v-btn v-bind="props" flat size="small" color="white">
              <v-icon size="small" start> mdi-account-circle </v-icon>
              {{ user }}
              <v-icon size="small" end> mdi-chevron-down </v-icon>
            </v-btn>
          </template>
          <v-list bg-color="primary" dark nav>
            <v-list-item to="/change-password">
              <template v-slot:prepend>
                <v-icon small>mdi-form-textbox-password</v-icon>
              </template>
              <v-list-item-title>Change password</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item @click="logOut">
              <template v-slot:prepend>
                <v-icon small>mdi-logout-variant</v-icon>
              </template>
              <v-list-item-title>Log out</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </v-app-bar>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </v-app>
</template>

<script>
export default {
  name: "App",
  computed: {
    user() {
      return this.$store.state.user;
    },
  },
  methods: {
    logOut() {
      this.$logger.info(`Log out user ${this.user}`);
      this.$store.dispatch("logout");
    },
  },
  watch: {
    $route: {
      immediate: true,
      handler(to) {
        document.title = to.meta.title || "Sorting Hat";
      },
    },
  },
};
</script>
<style lang="scss">
@import "styles/index.scss";
.fade-enter-active,
.fade-leave-active {
  transition-duration: 0.3s;
  transition-property: opacity;
  transition-timing-function: ease;
}

.fade-enter,
.fade-leave-active {
  opacity: 0;
}
.pointer {
  cursor: pointer;
}
</style>
