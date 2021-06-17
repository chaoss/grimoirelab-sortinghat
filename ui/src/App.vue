<template>
  <v-app>
    <v-app-bar app color="primary" dark dense flat class="pl-6 pr-6">
      <router-link to="/" v-slot="{ href, navigate }">
        <h1 :href="href" @click="navigate" class="text-h6 pointer">
          Sorting Hat
        </h1>
      </router-link>

      <v-spacer></v-spacer>
      <v-menu v-if="user && $route.name !== 'Login'" offset-y>
        <template v-slot:activator="{ on }">
          <v-btn depressed small color="primary" v-on="on">
            <v-icon small left>
              mdi-account-circle
            </v-icon>
            {{ user }}
            <v-icon small right>
              mdi-chevron-down
            </v-icon>
          </v-btn>
        </template>
        <v-list color="primary" dark dense>
          <v-list-item to="/">
            <v-list-item-icon class="mr-2">
              <v-icon small>mdi-view-dashboard-variant</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Dashboard</v-list-item-title>
          </v-list-item>
          <v-divider />
          <v-list-item to="/jobs">
            <v-list-item-icon class="mr-2">
              <v-icon small>mdi-tray-full</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Jobs</v-list-item-title>
          </v-list-item>
          <v-divider />
          <v-list-item @click="logOut">
            <v-list-item-icon class="mr-2">
              <v-icon small>mdi-logout-variant</v-icon>
            </v-list-item-icon>
            <v-list-item-title>Log out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <transition name="fade" mode="out-in">
      <router-view />
    </transition>
  </v-app>
</template>

<script>
import Cookies from "js-cookie";
export default {
  name: "App",
  computed: {
    user() {
      return this.$store.state.user;
    }
  },
  methods: {
    logOut() {
      Cookies.remove("sh_authtoken");
      Cookies.remove("sh_user");
      this.$store.commit("setToken", undefined);
      this.$store.commit("loginUser", undefined);
      this.$router.push("/login");
      this.$logger.info(`Log out user ${this.user}`);
    }
  },
  watch: {
    $route: {
      immediate: true,
      handler(to) {
        document.title = to.meta.title || "Sorting Hat";
      }
    }
  }
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
